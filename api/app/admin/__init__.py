"""Admin do conteúdo. Só é montado com ADMIN_HABILITADO=true.

Antes de ir para produção, precisa estar protegido pelo Keycloak (bloqueio de deploy).
"""
from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqlalchemy import Engine, inspect

from app.db.catalogo import (
    Categoria,
    Estado,
    FaseRoteiro,
    Item,
    ItemMarca,
    ItemRegra,
    ItemTamanho,
    JanelaTamanho,
    Marca,
    Municipio,
    PerfilClima,
    RegraSeguranca,
)


class ItemAdmin(ModelView, model=Item):
    name, name_plural, icon = "Item", "Itens", "fa-solid fa-baby"
    column_list = [Item.nome, Item.categoria, Item.prioridade_base, Item.e_seguranca]
    column_searchable_list = [Item.nome, Item.slug]
    column_sortable_list = [Item.nome, Item.prioridade_base]
    # Tamanhos, regras e marcas têm telas próprias; listá-los aqui misturaria os de outros itens.
    form_excluded_columns = [Item.tamanhos, Item.regras, Item.marcas]


class ItemTamanhoAdmin(ModelView, model=ItemTamanho):
    name, name_plural, icon = "Quantidade por tamanho", "Quantidades por tamanho", "fa-solid fa-ruler"
    column_list = [ItemTamanho.item, ItemTamanho.tamanho, ItemTamanho.quantidade_base]


class ItemRegraAdmin(ModelView, model=ItemRegra):
    name, name_plural, icon = "Regra do item", "Regras dos itens", "fa-solid fa-code-branch"
    column_list = [ItemRegra.item, ItemRegra.condicao, ItemRegra.efeito, ItemRegra.valor]


class MarcaAdmin(ModelView, model=Marca):
    name, name_plural, icon = "Marca", "Marcas", "fa-solid fa-tag"
    column_list = [Marca.nome, Marca.faixa_padrao, Marca.validado, Marca.revisado_em]
    column_searchable_list = [Marca.nome]
    column_sortable_list = [Marca.nome, Marca.validado]
    form_excluded_columns = [Marca.vinculos]


class ItemMarcaAdmin(ModelView, model=ItemMarca):
    name, name_plural, icon = "Marca do item", "Marcas dos itens", "fa-solid fa-link"
    column_list = [ItemMarca.item, ItemMarca.marca, ItemMarca.faixa, ItemMarca.ordem]


class RegraSegurancaAdmin(ModelView, model=RegraSeguranca):
    name, name_plural, icon = "Regra de segurança", "Regras de segurança", "fa-solid fa-shield-heart"
    column_list = [
        RegraSeguranca.codigo,
        RegraSeguranca.tema,
        RegraSeguranca.idade_inicio_meses,
        RegraSeguranca.idade_fim_meses,
        RegraSeguranca.validado,
    ]


class CategoriaAdmin(ModelView, model=Categoria):
    name, name_plural, icon = "Categoria", "Categorias", "fa-solid fa-layer-group"
    column_list = [Categoria.nome, Categoria.ordem]


class FaseRoteiroAdmin(ModelView, model=FaseRoteiro):
    name, name_plural, icon = "Fase do roteiro", "Fases do roteiro", "fa-solid fa-route"
    column_list = [FaseRoteiro.ordem, FaseRoteiro.nome, FaseRoteiro.inicio, FaseRoteiro.fim]


class JanelaTamanhoAdmin(ModelView, model=JanelaTamanho):
    name, name_plural, icon = "Janela de tamanho", "Janelas de tamanho", "fa-solid fa-calendar"
    column_list = [
        JanelaTamanho.tamanho,
        JanelaTamanho.idade_inicio_dias,
        JanelaTamanho.idade_fim_dias,
    ]


class PerfilClimaAdmin(ModelView, model=PerfilClima):
    name, name_plural, icon = "Perfil de clima", "Perfis de clima", "fa-solid fa-temperature-half"
    column_list = [PerfilClima.nome, PerfilClima.meses_frios, PerfilClima.meses_frescos]


class EstadoAdmin(ModelView, model=Estado):
    name, name_plural, icon = "Estado", "Estados", "fa-solid fa-map"
    column_list = [Estado.uf, Estado.nome, Estado.perfil_padrao]


class MunicipioAdmin(ModelView, model=Municipio):
    name, name_plural, icon = "Município", "Municípios", "fa-solid fa-city"
    column_list = [Municipio.nome, Municipio.uf, Municipio.perfil_excecao]
    column_searchable_list = [Municipio.nome, Municipio.nome_busca]
    form_excluded_columns = [Municipio.nome_busca]


VISOES = [
    ItemAdmin,
    ItemTamanhoAdmin,
    ItemRegraAdmin,
    MarcaAdmin,
    ItemMarcaAdmin,
    RegraSegurancaAdmin,
    CategoriaAdmin,
    FaseRoteiroAdmin,
    JanelaTamanhoAdmin,
    PerfilClimaAdmin,
    EstadoAdmin,
    MunicipioAdmin,
]


ROTULOS = {
    "id": "ID", "slug": "Identificador", "nome": "Nome", "ordem": "Ordem", "codigo": "Código",
    "referencia": "Referência", "inicio": "Início", "fim": "Fim", "texto": "Texto",
    "categoria_id": "Categoria", "categoria": "Categoria",
    "fase_compra_id": "Fase de compra", "fase_compra": "Fase de compra",
    "para_que_serve": "Para que serve", "como_escolher": "Como escolher",
    "idade_inicio_meses": "Idade inicial (meses)", "idade_fim_meses": "Idade final (meses)",
    "prioridade_base": "Prioridade", "e_seguranca": "É item de segurança",
    "uso_clima": "Uso conforme o clima", "variante_frio": "Variante para o frio",
    "variante_calor": "Variante para o calor", "escala_lavagem": "Quantidade segue a lavagem",
    "quantidade": "Quantidade", "unidade_texto": "Unidade", "item_id": "Item", "item": "Item",
    "itens": "Itens", "tamanho": "Tamanho", "tamanhos": "Quantidades por tamanho",
    "quantidade_base": "Quantidade base", "condicao": "Condição", "efeito": "Efeito",
    "valor": "Valor", "regras": "Regras", "marcas": "Marcas", "marca_id": "Marca",
    "marca": "Marca", "vinculos": "Itens que usam a marca", "faixa": "Faixa",
    "faixa_padrao": "Faixa padrão", "validado": "Validado", "fonte": "Fonte",
    "revisado_em": "Revisado em", "regras_seguranca": "Regras de segurança", "tema": "Tema",
    "base": "Base", "idade_inicio_dias": "Idade inicial (dias)",
    "idade_fim_dias": "Idade final (dias)", "peso_referencia": "Peso de referência",
    "descricao": "Descrição", "meses_frios": "Meses frios", "meses_frescos": "Meses frescos",
    "uf": "UF", "perfil_padrao": "Perfil padrão", "codigo_ibge": "Código IBGE",
    "nome_busca": "Nome para busca", "perfil_excecao": "Perfil de exceção",
    "estado": "Estado",
}


def _rotulos(modelo: type) -> dict:
    mapa = inspect(modelo)
    nomes = [a.key for a in mapa.column_attrs] + [r.key for r in mapa.relationships]
    return {
        getattr(modelo, nome): ROTULOS.get(nome, nome.replace("_", " ").capitalize())
        for nome in nomes
    }


for _visao in VISOES:
    _visao.column_labels = _rotulos(_visao.model)


def montar_admin(app: FastAPI, engine: Engine) -> None:
    admin = Admin(app, engine, base_url="/admin", title="Enxoval Inteligente · Conteúdo")
    for visao in VISOES:
        admin.add_view(visao)
