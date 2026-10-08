"""Serviço de domínio para o Enxoval: orquestra repositório, motor e validações.

Centraliza todas as operações sobre enxovais, incluindo controle de acesso
por proprietário (``dono_id``) quando a autenticação Keycloak está ativa.
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
    - Criar, editar, apagar e ler enxovais com controle de acesso por dono.
    - Listar enxovais do usuário autenticado.
    - Marcar e completar linhas da planilha.
    - Validar dados de domínio (data prevista, município, quantidades).

    Args:
        sessao: Sessão SQLAlchemy ativa.
        hoje: Data de referência para cálculos de fase e validações.
        dono_id: ``sub`` do JWT Keycloak do usuário logado, ou ``None`` em dev.
    """

    def __init__(self, sessao: Session, hoje: date, dono_id: str | None = None) -> None:
        self._sessao = sessao
        self._hoje = hoje
        self._dono_id = dono_id
        self._repo = EnxovalRepository(sessao)

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def ler(self, enxoval_id: uuid.UUID) -> EnxovalCompleto:
        """Monta o enxoval completo verificando a posse.

        Args:
            enxoval_id: UUID do enxoval a ser lido.

        Returns:
            ``EnxovalCompleto`` com motor calculado, progresso e catálogo.

        Raises:
            EnxovalNaoEncontrado: Se o UUID não existir ou pertencer a outro dono.
        """
        enxoval = self._repo.buscar_por_id_e_dono(enxoval_id, self._dono_id)
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

    def listar(self) -> list[Enxoval]:
        """Lista os enxovais do usuário logado, do mais recente ao mais antigo.

        Em modo dev sem autenticação, retorna todos os enxovais do banco.

        Returns:
            Lista de ``Enxoval`` sem as linhas carregadas (apenas metadados).
        """
        return self._repo.listar_por_dono(self._dono_id)

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
        """Cria um novo enxoval vinculado ao usuário logado.

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
            dono_id=self._dono_id,
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
        """Substitui as respostas verificando a posse do enxoval.

        Args:
            enxoval_id: UUID do enxoval a editar.
            (demais parâmetros: idênticos a ``criar``)

        Raises:
            EnxovalNaoEncontrado: Se o UUID não existir ou pertencer a outro dono.
            DadoInvalido: Se a data, o município ou o estado estiverem inválidos.
        """
        enxoval = self._repo.buscar_por_id_e_dono(enxoval_id, self._dono_id)
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
        """Remove o enxoval verificando a posse.

        Raises:
            EnxovalNaoEncontrado: Se o UUID não existir ou pertencer a outro dono.
        """
        self._repo.apagar(self._repo.buscar_por_id_e_dono(enxoval_id, self._dono_id))

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
        """Grava as quantidades de uma linha verificando a posse do enxoval."""
        if min(comprada, ganhada, ja_tinha) < 0:
            raise DadoInvalido("quantidade_negativa", "As quantidades não podem ser negativas.")
        enxoval = self._repo.buscar_por_id_e_dono(enxoval_id, self._dono_id)
        linha = self._repo.buscar_ou_criar_linha(enxoval, chave)
        linha.qtd_comprada = comprada
        linha.qtd_ganhada = ganhada
        linha.qtd_ja_tinha = ja_tinha
        self._repo.salvar_linha(linha)

    def completar_linha(self, enxoval_id: uuid.UUID, chave: str, origem: str) -> None:
        """Completa o que falta em uma linha verificando a posse do enxoval."""
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
        """Verifica que a data prevista está na janela permitida."""
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
        """Resolve o perfil de clima a partir do município e da correção manual."""
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
