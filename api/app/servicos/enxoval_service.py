"""Serviço de domínio para o Enxoval: orquestra repositório, motor e validações.

O ``EnxovalService`` centraliza as operações de domínio que antes estavam
espalhadas em funções livres em ``servicos/escrita.py`` e ``servicos/leitura.py``.
A divisão em classe facilita:

- **Injeção de dependência:** o repositório pode ser trocado por um mock em testes.
- **Coesão:** todas as operações sobre um enxoval ficam num único lugar.
- **Testabilidade:** métodos podem ser testados individualmente.

As funções livres existentes (``criar_enxoval``, ``ler_enxoval``, etc.) continuam
funcionando — elas delegam para este serviço para manter retrocompatibilidade
com as rotas durante a transição.
"""
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.db.catalogo import Estado, Municipio
from app.db.enums import Faixa, Moradia, PerfilCodigo
from app.db.familia import Enxoval
from app.erros import DadoInvalido
from app.motor.calendario import adicionar_meses
from app.motor.clima import resolver_perfil
from app.motor.montagem import montar_enxoval
from app.motor.progresso import Marcacao, progresso
from app.repositorios.enxoval import EnxovalRepository
from app.servicos.catalogo import carregar_catalogo, perfis_por_codigo
from app.servicos.leitura import EnxovalCompleto

MESES_A_FRENTE = 10
ANOS_ATRAS = 1
ORIGENS_VALIDAS = frozenset({"comprada", "ganhada", "ja_tinha"})
COLUNA_DA_ORIGEM = {
    "comprada": "qtd_comprada",
    "ganhada": "qtd_ganhada",
    "ja_tinha": "qtd_ja_tinha",
}


class EnxovalService:
    """Serviço de domínio para operações sobre o Enxoval.

    Responsabilidades:
    - Criar, editar e apagar enxovais.
    - Ler o enxoval completo (calculado + marcações).
    - Marcar e completar linhas da planilha.
    - Validar dados de domínio (data prevista, município, quantidades).

    Args:
        sessao: Sessão SQLAlchemy ativa.
        hoje: Data de referência para cálculos de fase e validações.
    """

    def __init__(self, sessao: Session, hoje: date) -> None:
        self._sessao = sessao
        self._hoje = hoje
        self._repo = EnxovalRepository(sessao)

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def ler(self, enxoval_id: uuid.UUID) -> EnxovalCompleto:
        """Monta o enxoval completo: calcula a lista e mescla com as marcações.

        Args:
            enxoval_id: UUID do enxoval a ser lido.

        Returns:
            ``EnxovalCompleto`` com motor calculado, progresso e catálogo.

        Raises:
            EnxovalNaoEncontrado: Se o UUID não existir.
        """
        enxoval = self._repo.buscar_por_id(enxoval_id)
        municipio = self._sessao.get(Municipio, enxoval.municipio_codigo)
        perfis = perfis_por_codigo(self._sessao)
        from app.motor.tipos import PerfilClima as PerfilClimaTipo
        perfil = perfis.get(
            enxoval.perfil_clima,
            PerfilClimaTipo(enxoval.perfil_clima, frozenset(), frozenset()),
        )

        catalogo = carregar_catalogo(self._sessao)
        from app.servicos.leitura import respostas_do_motor
        calculado = montar_enxoval(respostas_do_motor(enxoval, perfil), catalogo, self._hoje)

        marcadas = {
            linha.chave: Marcacao(
                comprada=linha.qtd_comprada,
                ganhada=linha.qtd_ganhada,
                ja_tinha=linha.qtd_ja_tinha,
            )
            for linha in enxoval.linhas
        }
        resultado = progresso(calculado.linhas, marcadas)
        fora = tuple(l for l in enxoval.linhas if l.chave in set(resultado.fora_da_lista))

        return EnxovalCompleto(
            enxoval=enxoval,
            municipio=municipio,
            perfil=perfil,
            calculado=calculado,
            marcadas=marcadas,
            progresso=resultado,
            fora_da_lista=tuple(sorted(fora, key=lambda l: l.chave)),
            catalogo=catalogo,
        )

    # ------------------------------------------------------------------
    # Escrita — Enxoval
    # ------------------------------------------------------------------

    def criar(
        self,
        municipio_codigo: int,
        data_prevista: date,
        dias_entre_lavagens: int,
        moradia: Moradia,
        tem_carro: bool,
        orcamento: Faixa,
        primeiro_filho: bool,
        correcao_perfil: PerfilCodigo | None = None,
    ) -> Enxoval:
        """Cria um novo enxoval após validar os dados e resolver o perfil de clima.

        Args:
            municipio_codigo: Código IBGE do município.
            data_prevista: Data prevista de nascimento.
            dias_entre_lavagens: Frequência de lavagem (1–7 dias).
            moradia: Tipo de moradia da família.
            tem_carro: Se a família tem carro.
            orcamento: Faixa de orçamento.
            primeiro_filho: Se é o primeiro filho.
            correcao_perfil: Perfil de clima corrigido manualmente (opcional).

        Returns:
            Instância ORM de Enxoval com ID gerado após flush.

        Raises:
            DadoInvalido: Se a data, o município ou o estado estiverem inválidos.
        """
        self._validar_data(data_prevista)
        perfil, corrigido = self._resolver_perfil(municipio_codigo, correcao_perfil)
        enxoval = Enxoval(
            municipio_codigo=municipio_codigo,
            perfil_clima=perfil,
            perfil_corrigido=corrigido,
            data_prevista=data_prevista,
            dias_entre_lavagens=dias_entre_lavagens,
            moradia=moradia,
            tem_carro=tem_carro,
            orcamento=orcamento,
            primeiro_filho=primeiro_filho,
        )
        return self._repo.criar(enxoval)

    def editar(
        self,
        enxoval_id: uuid.UUID,
        municipio_codigo: int,
        data_prevista: date,
        dias_entre_lavagens: int,
        moradia: Moradia,
        tem_carro: bool,
        orcamento: Faixa,
        primeiro_filho: bool,
        correcao_perfil: PerfilCodigo | None = None,
    ) -> Enxoval:
        """Substitui as respostas de um enxoval existente.

        As quantidades marcadas são preservadas — a lista é recalculada
        na próxima leitura com as novas respostas.

        Args:
            enxoval_id: UUID do enxoval a editar.
            (demais parâmetros: idênticos a ``criar``)

        Returns:
            Instância ORM de Enxoval após o flush.

        Raises:
            EnxovalNaoEncontrado: Se o UUID não existir.
            DadoInvalido: Se a data, o município ou o estado estiverem inválidos.
        """
        enxoval = self._repo.buscar_por_id(enxoval_id)
        self._validar_data(data_prevista)
        perfil, corrigido = self._resolver_perfil(municipio_codigo, correcao_perfil)
        enxoval.municipio_codigo = municipio_codigo
        enxoval.perfil_clima = perfil
        enxoval.perfil_corrigido = corrigido
        enxoval.data_prevista = data_prevista
        enxoval.dias_entre_lavagens = dias_entre_lavagens
        enxoval.moradia = moradia
        enxoval.tem_carro = tem_carro
        enxoval.orcamento = orcamento
        enxoval.primeiro_filho = primeiro_filho
        self._sessao.flush()
        return enxoval

    def apagar(self, enxoval_id: uuid.UUID) -> None:
        """Remove o enxoval e todas as suas linhas.

        Args:
            enxoval_id: UUID do enxoval a apagar.

        Raises:
            EnxovalNaoEncontrado: Se o UUID não existir.
        """
        self._repo.apagar(self._repo.buscar_por_id(enxoval_id))

    # ------------------------------------------------------------------
    # Escrita — Linhas
    # ------------------------------------------------------------------

    def marcar_linha(
        self,
        enxoval_id: uuid.UUID,
        chave: str,
        comprada: int,
        ganhada: int,
        ja_tinha: int,
    ) -> None:
        """Grava as quantidades de uma linha da planilha.

        Aceita chave que não está na lista atual para preservar marcações
        de famílias que mudaram de respostas (linhas órfãs).

        Args:
            enxoval_id: UUID do enxoval.
            chave: Chave da linha (``<slug>:<tamanho>:<variante>``).
            comprada: Unidades compradas.
            ganhada: Unidades ganhas.
            ja_tinha: Unidades que já existiam em casa.

        Raises:
            EnxovalNaoEncontrado: Se o UUID não existir.
            DadoInvalido: Se alguma quantidade for negativa.
        """
        if min(comprada, ganhada, ja_tinha) < 0:
            raise DadoInvalido("quantidade_negativa", "As quantidades não podem ser negativas.")
        enxoval = self._repo.buscar_por_id(enxoval_id)
        linha = self._repo.buscar_ou_criar_linha(enxoval, chave)
        linha.qtd_comprada = comprada
        linha.qtd_ganhada = ganhada
        linha.qtd_ja_tinha = ja_tinha
        self._repo.salvar_linha(linha)

    def completar_linha(self, enxoval_id: uuid.UUID, chave: str, origem: str) -> None:
        """Completa o que falta em uma linha com a origem informada ("marcar tudo").

        Args:
            enxoval_id: UUID do enxoval.
            chave: Chave da linha a completar.
            origem: Como contabilizar o restante: ``'comprada'``, ``'ganhada'``
                ou ``'ja_tinha'``.

        Raises:
            EnxovalNaoEncontrado: Se o UUID não existir.
            DadoInvalido: Se a origem for inválida ou a chave não estiver na lista.
        """
        if origem not in ORIGENS_VALIDAS:
            raise DadoInvalido(
                "origem_invalida",
                "Informe se o item foi comprado, ganhado ou se você já tinha.",
            )
        completo = self.ler(enxoval_id)
        calculada = next((l for l in completo.calculado.linhas if l.chave == chave), None)
        if calculada is None:
            raise DadoInvalido("linha_nao_encontrada", "Este item não está na sua lista atual.")

        linha = self._repo.buscar_ou_criar_linha(completo.enxoval, chave)
        ja_tem = linha.qtd_comprada + linha.qtd_ganhada + linha.qtd_ja_tinha
        falta = max(0, calculada.quantidade - ja_tem)
        coluna = COLUNA_DA_ORIGEM[origem]
        setattr(linha, coluna, getattr(linha, coluna) + falta)
        self._repo.salvar_linha(linha)

    # ------------------------------------------------------------------
    # Validações privadas
    # ------------------------------------------------------------------

    def _validar_data(self, data_prevista: date) -> None:
        """Verifica que a data prevista está na janela permitida.

        Args:
            data_prevista: Data a validar.

        Raises:
            DadoInvalido: Se a data estiver fora da janela de 1 ano atrás
                a 10 meses à frente.
        """
        minimo = adicionar_meses(self._hoje, -12 * ANOS_ATRAS)
        maximo = adicionar_meses(self._hoje, MESES_A_FRENTE)
        if not minimo <= data_prevista <= maximo:
            raise DadoInvalido(
                "data_prevista_fora_da_faixa",
                "A data prevista precisa estar entre um ano atrás e 10 meses à frente de hoje.",
            )

    def _resolver_perfil(
        self,
        municipio_codigo: int,
        correcao: PerfilCodigo | None,
    ) -> tuple[PerfilCodigo, bool]:
        """Resolve o perfil de clima a partir do município e da correção manual.

        Args:
            municipio_codigo: Código IBGE do município.
            correcao: Perfil de clima corrigido manualmente (ou ``None``).

        Returns:
            Tupla ``(perfil_codigo, foi_corrigido)``.

        Raises:
            DadoInvalido: Se o município ou o estado não forem encontrados.
        """
        municipio = self._sessao.get(Municipio, municipio_codigo)
        if municipio is None:
            raise DadoInvalido(
                "municipio_nao_encontrado",
                "Não encontramos esta cidade. Escolha uma da lista.",
            )
        estado = self._sessao.get(Estado, municipio.uf)
        if estado is None:
            raise DadoInvalido(
                "estado_nao_encontrado",
                "O cadastro desta cidade está incompleto. Escolha outra cidade por enquanto.",
            )
        perfil = resolver_perfil(municipio.perfil_excecao, estado.perfil_padrao, correcao)
        return perfil, correcao is not None
