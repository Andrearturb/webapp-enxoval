from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.catalogo import Item, RegraSeguranca
from app.db.enums import TemaSeguranca
from seed.util import buscar, enum_de, ler_yaml, validar_campos


CAMPOS_OBRIGATORIOS = {
    "codigo", "tema", "idade_inicio_meses", "idade_fim_meses", "texto", "base",
}
CAMPOS_OPCIONAIS = {"itens"}


def carregar_seguranca(sessao: Session, dados: list | None = None) -> dict[str, int]:
    itens = {i.slug: i for i in sessao.scalars(select(Item))}
    existentes = set(sessao.scalars(select(RegraSeguranca.codigo)))
    novas = 0
    for bruto in dados if dados is not None else ler_yaml("seguranca.yaml"):
        ctx = f"regra '{bruto.get('codigo', '?')}'"
        validar_campos(bruto, CAMPOS_OBRIGATORIOS, CAMPOS_OPCIONAIS, ctx)
        codigo = bruto["codigo"]
        if codigo in existentes:
            continue
        sessao.add(
            RegraSeguranca(
                codigo=codigo,
                tema=enum_de(TemaSeguranca, bruto["tema"], ctx),
                idade_inicio_meses=bruto["idade_inicio_meses"],
                idade_fim_meses=bruto["idade_fim_meses"],
                texto=bruto["texto"],
                base=bruto["base"],
                itens=[buscar(itens, slug, ctx, "item") for slug in bruto.get("itens", [])],
            )
        )
        novas += 1
    sessao.flush()
    return {"regra_seguranca": novas}
