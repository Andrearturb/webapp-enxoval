import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.db.catalogo import Estado, Municipio
from app.db.enums import Faixa, Moradia, PerfilCodigo
from app.db.familia import Enxoval, EnxovalLinha
from app.erros import DadoInvalido
from app.motor.calendario import adicionar_meses
from app.motor.clima import resolver_perfil
from app.servicos.leitura import buscar_enxoval, ler_enxoval

MESES_A_FRENTE = 10
ANOS_ATRAS = 1
ORIGENS = ("comprada", "ganhada", "ja_tinha")
COLUNA_DA_ORIGEM = {
    "comprada": "qtd_comprada",
    "ganhada": "qtd_ganhada",
    "ja_tinha": "qtd_ja_tinha",
}


@dataclass(frozen=True)
class DadosRespostas:
    municipio_codigo: int
    data_prevista: date
    dias_entre_lavagens: int
    moradia: Moradia
    tem_carro: bool
    orcamento: Faixa
    primeiro_filho: bool
    correcao_perfil: PerfilCodigo | None = None


def _validar_data(data_prevista: date, hoje: date) -> None:
    minimo = adicionar_meses(hoje, -12 * ANOS_ATRAS)
    maximo = adicionar_meses(hoje, MESES_A_FRENTE)
    if not minimo <= data_prevista <= maximo:
        raise DadoInvalido(
            "data_prevista_fora_da_faixa",
            "A data prevista precisa estar entre um ano atrás e 10 meses à frente de hoje.",
        )


def _resolver(sessao: Session, dados: DadosRespostas) -> tuple[PerfilCodigo, bool]:
    municipio = sessao.get(Municipio, dados.municipio_codigo)
    if municipio is None:
        raise DadoInvalido(
            "municipio_nao_encontrado", "Não encontramos esta cidade. Escolha uma da lista."
        )
    estado = sessao.get(Estado, municipio.uf)
    if estado is None:
        raise DadoInvalido(
            "estado_nao_encontrado",
            "O cadastro desta cidade está incompleto. Escolha outra cidade por enquanto.",
        )
    perfil = resolver_perfil(
        municipio.perfil_excecao, estado.perfil_padrao, dados.correcao_perfil
    )
    return perfil, dados.correcao_perfil is not None


def _aplicar(enxoval: Enxoval, dados: DadosRespostas, perfil: PerfilCodigo, corrigido: bool) -> None:
    enxoval.municipio_codigo = dados.municipio_codigo
    enxoval.perfil_clima = perfil
    enxoval.perfil_corrigido = corrigido
    enxoval.data_prevista = dados.data_prevista
    enxoval.dias_entre_lavagens = dados.dias_entre_lavagens
    enxoval.moradia = dados.moradia
    enxoval.tem_carro = dados.tem_carro
    enxoval.orcamento = dados.orcamento
    enxoval.primeiro_filho = dados.primeiro_filho


def criar_enxoval(sessao: Session, dados: DadosRespostas, hoje: date) -> Enxoval:
    _validar_data(dados.data_prevista, hoje)
    perfil, corrigido = _resolver(sessao, dados)
    enxoval = Enxoval(
        municipio_codigo=dados.municipio_codigo,
        perfil_clima=perfil,
        perfil_corrigido=corrigido,
        data_prevista=dados.data_prevista,
        dias_entre_lavagens=dados.dias_entre_lavagens,
        moradia=dados.moradia,
        tem_carro=dados.tem_carro,
        orcamento=dados.orcamento,
        primeiro_filho=dados.primeiro_filho,
    )
    sessao.add(enxoval)
    sessao.flush()
    return enxoval


def editar_respostas(
    sessao: Session, enxoval_id: uuid.UUID, dados: DadosRespostas, hoje: date
) -> Enxoval:
    """Troca as respostas. As quantidades marcadas ficam: a lista é recalculada na leitura."""
    enxoval = buscar_enxoval(sessao, enxoval_id)
    _validar_data(dados.data_prevista, hoje)
    perfil, corrigido = _resolver(sessao, dados)
    _aplicar(enxoval, dados, perfil, corrigido)
    sessao.flush()
    return enxoval


def _linha(sessao: Session, enxoval: Enxoval, chave: str) -> EnxovalLinha:
    for linha in enxoval.linhas:
        if linha.chave == chave:
            return linha
    # qtd_* ficariam None em memória até o flush aplicar o default da coluna;
    # completar_linha soma essas quantidades antes de qualquer flush.
    linha = EnxovalLinha(chave=chave, qtd_comprada=0, qtd_ganhada=0, qtd_ja_tinha=0)
    enxoval.linhas.append(linha)
    return linha


def marcar_linha(
    sessao: Session,
    enxoval_id: uuid.UUID,
    chave: str,
    comprada: int,
    ganhada: int,
    ja_tinha: int,
) -> EnxovalLinha:
    """Grava as quantidades de uma linha.

    Aceita chave que não está na lista atual: a família pode ter mudado de cidade, e
    perder o que ela marcou é pior do que guardar uma linha órfã.
    """
    enxoval = buscar_enxoval(sessao, enxoval_id)
    if min(comprada, ganhada, ja_tinha) < 0:
        raise DadoInvalido("quantidade_negativa", "As quantidades não podem ser negativas.")
    linha = _linha(sessao, enxoval, chave)
    linha.qtd_comprada = comprada
    linha.qtd_ganhada = ganhada
    linha.qtd_ja_tinha = ja_tinha
    sessao.flush()
    return linha


def completar_linha(
    sessao: Session, enxoval_id: uuid.UUID, chave: str, origem: str, hoje: date
) -> EnxovalLinha:
    """Completa o que falta na linha com a origem informada ("marcar tudo")."""
    if origem not in ORIGENS:
        raise DadoInvalido(
            "origem_invalida",
            "Informe se o item foi comprado, ganhado ou se você já tinha.",
        )
    completo = ler_enxoval(sessao, enxoval_id, hoje)
    calculada = next((l for l in completo.calculado.linhas if l.chave == chave), None)
    if calculada is None:
        raise DadoInvalido(
            "linha_nao_encontrada", "Este item não está na sua lista atual."
        )
    linha = _linha(sessao, completo.enxoval, chave)
    ja_tem = linha.qtd_comprada + linha.qtd_ganhada + linha.qtd_ja_tinha
    falta = max(0, calculada.quantidade - ja_tem)
    coluna = COLUNA_DA_ORIGEM[origem]
    setattr(linha, coluna, getattr(linha, coluna) + falta)
    sessao.flush()
    return linha


def apagar_enxoval(sessao: Session, enxoval_id: uuid.UUID) -> None:
    sessao.delete(buscar_enxoval(sessao, enxoval_id))
    sessao.flush()
