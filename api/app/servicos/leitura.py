import logging
import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.catalogo import Municipio
from app.db.familia import Enxoval, EnxovalLinha
from app.erros import EnxovalNaoEncontrado
from app.motor.montagem import montar_enxoval
from app.motor.progresso import Marcacao, Progresso, progresso
from app.motor.tipos import Catalogo, EnxovalCalculado, PerfilClima, Respostas
from app.servicos.catalogo import carregar_catalogo, perfis_por_codigo

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EnxovalCompleto:
    enxoval: Enxoval
    municipio: Municipio
    perfil: PerfilClima
    calculado: EnxovalCalculado
    marcadas: dict[str, Marcacao]
    progresso: Progresso
    fora_da_lista: tuple[EnxovalLinha, ...]
    catalogo: Catalogo


def respostas_do_motor(enxoval: Enxoval, perfil: PerfilClima) -> Respostas:
    return Respostas(
        perfil=perfil,
        data_prevista=enxoval.data_prevista,
        dias_entre_lavagens=enxoval.dias_entre_lavagens,
        moradia=enxoval.moradia,
        tem_carro=enxoval.tem_carro,
        orcamento=enxoval.orcamento,
        primeiro_filho=enxoval.primeiro_filho,
    )


def buscar_enxoval(sessao: Session, enxoval_id: uuid.UUID) -> Enxoval:
    enxoval = sessao.scalars(
        select(Enxoval)
        .where(Enxoval.id == enxoval_id)
        .options(selectinload(Enxoval.linhas))
    ).one_or_none()
    if enxoval is None:
        raise EnxovalNaoEncontrado()
    return enxoval


def ler_enxoval(sessao: Session, enxoval_id: uuid.UUID, hoje: date) -> EnxovalCompleto:
    """Monta a lista do zero e mescla o que a família marcou."""
    enxoval = buscar_enxoval(sessao, enxoval_id)
    municipio = sessao.get(Municipio, enxoval.municipio_codigo)
    perfis = perfis_por_codigo(sessao)
    perfil = perfis.get(
        enxoval.perfil_clima,
        PerfilClima(enxoval.perfil_clima, frozenset(), frozenset()),
    )
    if enxoval.perfil_clima not in perfis:
        logger.warning(
            "perfil de clima '%s' não encontrado no catálogo; sem meses frios/frescos",
            enxoval.perfil_clima,
        )

    catalogo = carregar_catalogo(sessao)
    if not catalogo.itens:
        # Banco migrado mas sem seed: a lista vem vazia (não é erro para a família),
        # mas quem opera precisa do sinal — sem isso, "python -m seed" esquecido
        # passaria em silêncio e toda família veria uma lista vazia. Sem o id.
        logger.warning("catálogo vazio no banco: confira se o seed foi executado")

    calculado = montar_enxoval(respostas_do_motor(enxoval, perfil), catalogo, hoje)

    for aviso in calculado.avisos:
        # Defeito de conteúdo, para quem edita o catálogo. Sem o id do enxoval.
        logger.warning("catálogo: %s", aviso)

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
