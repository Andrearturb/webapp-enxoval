from sqlalchemy import inspect

from app.admin import VISOES, ItemAdmin, MarcaAdmin
from app.db.catalogo import Item, ItemMarca, ItemRegra, ItemTamanho, Marca
from app.db.enums import Faixa


def test_itens_de_ligacao_tem_nome_legivel():
    item = Item(nome="Berço")
    marca = Marca(nome="Tcil")

    assert str(ItemMarca(item=item, marca=marca, faixa=Faixa.ECONOMICO)) == "Berço → Tcil (economico)"
    assert "Berço" in str(ItemTamanho(item=item, tamanho="P", quantidade_base=2))
    assert "Berço" in str(ItemRegra(item=item, condicao="sem_carro", efeito="dica"))


def test_formularios_nao_listam_as_ligacoes_de_outros_itens():
    assert {Item.tamanhos, Item.regras, Item.marcas} <= set(ItemAdmin.form_excluded_columns)
    assert Marca.vinculos in MarcaAdmin.form_excluded_columns


def test_todo_campo_tem_rotulo_em_portugues():
    for visao in VISOES:
        colunas = {a.key for a in inspect(visao.model).column_attrs}
        rotulos = {getattr(chave, "key", chave): texto for chave, texto in visao.column_labels.items()}
        assert colunas <= set(rotulos), f"{visao.__name__} sem rótulo para {colunas - set(rotulos)}"
        assert all("_" not in texto for texto in rotulos.values()), visao.__name__
    assert ItemAdmin.column_labels[Item.e_seguranca] == "É item de segurança"
