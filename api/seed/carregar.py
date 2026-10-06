from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.catalogo import Categoria, Item, Marca, Municipio, RegraSeguranca
from seed.base import carregar_base
from seed.cidades import aplicar_excecoes, carregar_municipios
from seed.itens import carregar_itens, carregar_marcas
from seed.seguranca import carregar_seguranca

ZERO_BASE = {
    "categoria": 0, "fase_roteiro": 0, "perfil_clima": 0, "janela_tamanho": 0, "estado": 0,
}
ZERO_ITENS = {"item": 0, "item_tamanho": 0, "item_regra": 0, "item_marca": 0}


def _vazia(sessao: Session, modelo: type) -> bool:
    return sessao.scalar(select(func.count()).select_from(modelo)) == 0


def carregar_tudo(sessao: Session, forcar: bool = False) -> dict[str, int]:
    """Carrega o conteúdo inicial, na ordem das dependências.

    Cada grupo só é carregado se a sua tabela ainda estiver vazia: depois da primeira
    carga o admin é a fonte da verdade, e o que foi apagado ou renomeado lá não volta.
    Com `forcar=True`, insere de novo o que estiver faltando (nunca sobrescreve).
    """
    resumo = dict(carregar_base(sessao) if forcar or _vazia(sessao, Categoria) else ZERO_BASE)
    resumo["marca"] = carregar_marcas(sessao) if forcar or _vazia(sessao, Marca) else 0
    resumo.update(carregar_itens(sessao) if forcar or _vazia(sessao, Item) else ZERO_ITENS)
    resumo["regra_seguranca"] = (
        carregar_seguranca(sessao)["regra_seguranca"]
        if forcar or _vazia(sessao, RegraSeguranca)
        else 0
    )
    resumo["municipio"] = (
        carregar_municipios(sessao) if forcar or _vazia(sessao, Municipio) else 0
    )
    # Exceções de clima só acompanham a carga dos municípios (o admin pode ter limpado alguma).
    resumo["municipio_excecao"] = (
        aplicar_excecoes(sessao) if forcar or resumo["municipio"] > 0 else 0
    )
    return resumo
