"""Converte as tabelas do catálogo nas dataclasses do motor.

Esta é a única direção: o motor nunca vê SQLAlchemy.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db import catalogo as tabelas
from app.db.enums import PerfilCodigo
from app.motor.tipos import (
    Catalogo,
    CategoriaCatalogo,
    Fase,
    ItemCatalogo,
    JanelaTamanho,
    MarcaDoItem,
    PerfilClima,
    RegraItem,
    RegraSegurancaCatalogo,
    TamanhoDoItem,
)


def perfis_por_codigo(sessao: Session) -> dict[PerfilCodigo, PerfilClima]:
    return {
        p.codigo: PerfilClima(
            codigo=p.codigo,
            meses_frios=frozenset(p.meses_frios or ()),
            meses_frescos=frozenset(p.meses_frescos or ()),
        )
        for p in sessao.scalars(select(tabelas.PerfilClima))
    }


def carregar_catalogo(sessao: Session) -> Catalogo:
    categorias = sessao.scalars(
        select(tabelas.Categoria).order_by(tabelas.Categoria.ordem)
    ).all()
    ordem_categoria = {c.id: c.ordem for c in categorias}

    itens = sessao.scalars(
        select(tabelas.Item).options(
            selectinload(tabelas.Item.tamanhos).selectinload(tabelas.ItemTamanho.fase_compra),
            selectinload(tabelas.Item.regras),
            selectinload(tabelas.Item.marcas).selectinload(tabelas.ItemMarca.marca),
            selectinload(tabelas.Item.regras_seguranca),
            joinedload(tabelas.Item.categoria),
            joinedload(tabelas.Item.fase_compra),
        )
    ).all()
    itens = sorted(itens, key=lambda i: (ordem_categoria.get(i.categoria_id, 10**6), i.ordem))

    return Catalogo(
        categorias=tuple(CategoriaCatalogo(c.slug, c.nome, c.ordem) for c in categorias),
        fases=tuple(
            Fase(f.codigo, f.nome, f.referencia, f.inicio, f.fim, f.texto, f.ordem)
            for f in sessao.scalars(
                select(tabelas.FaseRoteiro).order_by(tabelas.FaseRoteiro.ordem)
            )
        ),
        janelas=tuple(
            JanelaTamanho(j.tamanho, j.idade_inicio_dias, j.idade_fim_dias, j.peso_referencia)
            for j in sessao.scalars(select(tabelas.JanelaTamanho))
        ),
        itens=tuple(_item(i) for i in itens),
        regras_seguranca=tuple(
            RegraSegurancaCatalogo(
                codigo=r.codigo, tema=r.tema,
                idade_inicio_meses=r.idade_inicio_meses, idade_fim_meses=r.idade_fim_meses,
                texto=r.texto, base=r.base,
                itens=tuple(i.slug for i in r.itens),
            )
            for r in sessao.scalars(
                select(tabelas.RegraSeguranca)
                .options(selectinload(tabelas.RegraSeguranca.itens))
                .order_by(tabelas.RegraSeguranca.id)
            )
        ),
    )


def _item(item: tabelas.Item) -> ItemCatalogo:
    return ItemCatalogo(
        slug=item.slug,
        nome=item.nome,
        categoria_slug=item.categoria.slug,
        fase_codigo=item.fase_compra.codigo,
        ordem=item.ordem,
        para_que_serve=item.para_que_serve,
        como_escolher=item.como_escolher,
        prioridade_base=item.prioridade_base,
        idade_inicio_meses=item.idade_inicio_meses,
        e_seguranca=item.e_seguranca,
        uso_clima=item.uso_clima,
        variante_frio=item.variante_frio,
        variante_calor=item.variante_calor,
        escala_lavagem=item.escala_lavagem,
        quantidade=item.quantidade,
        unidade_texto=item.unidade_texto,
        tamanhos=tuple(
            TamanhoDoItem(
                tamanho=t.tamanho,
                quantidade_base=t.quantidade_base,
                fase_codigo=t.fase_compra.codigo if t.fase_compra else None,
            )
            for t in item.tamanhos
        ),
        regras=tuple(RegraItem(r.condicao, r.efeito, r.valor) for r in item.regras),
        marcas=tuple(
            MarcaDoItem(v.marca.nome, v.faixa, v.ordem) for v in item.marcas
        ),
        regras_seguranca=tuple(r.codigo for r in item.regras_seguranca),
    )
