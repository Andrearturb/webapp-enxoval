import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.catalogo import (
    Categoria,
    FaseRoteiro,
    Item,
    ItemMarca,
    ItemTamanho,
    Marca,
)
from app.db.enums import Faixa, Prioridade, ReferenciaFase, Tamanho, UsoClima


@pytest.fixture
def categoria_e_fase(sessao):
    categoria = Categoria(slug="roupas", nome="Roupas", ordem=1)
    fase = FaseRoteiro(
        codigo="gestacao_7_8m",
        nome="Do 7º ao 8º mês",
        referencia=ReferenciaFase.GESTACAO_SEMANA,
        inicio=27,
        fim=36,
        texto="Roupas RN e P.",
        ordem=3,
    )
    sessao.add_all([categoria, fase])
    sessao.flush()
    return categoria, fase


def _item(categoria, fase, **extra):
    dados = dict(
        slug="body",
        nome="Body",
        categoria=categoria,
        fase_compra=fase,
        prioridade_base=Prioridade.ESSENCIAL,
        uso_clima=UsoClima.DIVIDE,
        variante_frio="manga longa",
        variante_calor="manga curta",
        para_que_serve="Peça básica.",
        como_escolher="Algodão.",
    )
    dados.update(extra)
    return Item(**dados)


def test_item_com_tamanhos_e_valores_padrao(sessao, categoria_e_fase):
    categoria, fase = categoria_e_fase
    item = _item(categoria, fase)
    item.tamanhos.append(ItemTamanho(tamanho=Tamanho.RN, quantidade_base=4))
    sessao.add(item)
    sessao.flush()

    salvo = sessao.scalars(select(Item).where(Item.slug == "body")).one()
    assert salvo.categoria.nome == "Roupas"
    assert [t.tamanho for t in salvo.tamanhos] == [Tamanho.RN]
    assert salvo.e_seguranca is False
    assert salvo.escala_lavagem is False


def test_slug_de_item_e_unico(sessao, categoria_e_fase):
    categoria, fase = categoria_e_fase
    sessao.add(_item(categoria, fase))
    sessao.flush()
    sessao.add(_item(categoria, fase))
    with pytest.raises(IntegrityError):
        sessao.flush()


def test_item_que_divide_exige_as_duas_variantes(sessao, categoria_e_fase):
    categoria, fase = categoria_e_fase
    sessao.add(_item(categoria, fase, variante_calor=None))
    with pytest.raises(IntegrityError):
        sessao.flush()


def test_apagar_marca_remove_so_os_vinculos(sessao, categoria_e_fase):
    categoria, fase = categoria_e_fase
    marca = Marca(nome="Marca Teste", faixa_padrao=Faixa.ECONOMICO)
    item = _item(categoria, fase)
    item.marcas.append(ItemMarca(marca=marca, faixa=Faixa.ECONOMICO, ordem=1))
    sessao.add(item)
    sessao.flush()
    marca_id = marca.id
    assert marca.validado is False

    sessao.delete(marca)
    sessao.flush()
    sessao.expire_all()

    restante = sessao.scalars(select(Item).where(Item.slug == "body")).one()
    assert restante.marcas == []
    assert sessao.get(Marca, marca_id) is None
