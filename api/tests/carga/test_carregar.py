from sqlalchemy import select

from app.db.catalogo import Item, Marca, RegraSeguranca
from app.db.enums import TemaSeguranca
from seed.carregar import carregar_tudo


def test_carga_completa_e_idempotente(sessao):
    primeira = carregar_tudo(sessao)
    segunda = carregar_tudo(sessao)

    assert primeira["item"] == 48
    assert primeira["regra_seguranca"] == 8
    assert set(segunda.values()) == {0}


def test_regras_de_seguranca_ligadas_aos_itens(sessao):
    carregar_tudo(sessao)

    sono = sessao.scalars(
        select(RegraSeguranca).where(RegraSeguranca.codigo == "sono-seguro")
    ).one()
    assert sono.tema == TemaSeguranca.SONO
    assert sono.validado is False
    assert "berco" in {i.slug for i in sono.itens}

    conforto = sessao.scalars(select(Item).where(Item.slug == "bebe-conforto")).one()
    assert "transporte-bebe-conforto" in {r.codigo for r in conforto.regras_seguranca}


def test_recarga_preserva_edicao_feita_no_admin(sessao):
    carregar_tudo(sessao)
    marca = sessao.scalars(select(Marca).where(Marca.nome == "Tcil")).one()
    marca.validado = True
    marca.fonte = "site oficial, conferido"
    sessao.flush()

    carregar_tudo(sessao)
    sessao.expire_all()

    marca = sessao.scalars(select(Marca).where(Marca.nome == "Tcil")).one()
    assert marca.validado is True
    assert marca.fonte == "site oficial, conferido"


def test_item_apagado_no_admin_nao_volta_na_recarga(sessao):
    carregar_tudo(sessao)
    cinta = sessao.scalars(select(Item).where(Item.slug == "cinta-pos-parto")).one()
    sessao.delete(cinta)
    sessao.flush()

    carregar_tudo(sessao)

    assert sessao.scalars(select(Item).where(Item.slug == "cinta-pos-parto")).first() is None


def test_marca_renomeada_no_admin_nao_duplica_na_recarga(sessao):
    carregar_tudo(sessao)
    marca = sessao.scalars(select(Marca).where(Marca.nome == "Tcil")).one()
    marca.nome = "Tcil Móveis"
    sessao.flush()

    carregar_tudo(sessao)

    nomes = set(sessao.scalars(select(Marca.nome)))
    assert "Tcil Móveis" in nomes and "Tcil" not in nomes


def test_forcar_traz_de_volta_o_que_faltar(sessao):
    carregar_tudo(sessao)
    cinta = sessao.scalars(select(Item).where(Item.slug == "cinta-pos-parto")).one()
    sessao.delete(cinta)
    sessao.flush()

    resumo = carregar_tudo(sessao, forcar=True)

    assert resumo["item"] == 1
