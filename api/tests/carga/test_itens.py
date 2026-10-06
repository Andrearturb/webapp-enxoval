import pytest
from sqlalchemy import func, select

from app.db.catalogo import Item, Marca
from app.db.enums import Condicao, Efeito, Faixa, Prioridade, Tamanho, UsoClima
from seed.base import carregar_base
from seed.itens import carregar_itens, carregar_marcas

ITENS_DE_SEGURANCA = {
    "berco", "colchao-berco", "lencol-elastico", "bebe-conforto", "termometro",
    "protetor-tomada", "trava-gaveta", "portao-seguranca", "protetor-quina",
}


@pytest.fixture
def catalogo(sessao):
    carregar_base(sessao)
    carregar_marcas(sessao)
    carregar_itens(sessao)
    return sessao


def _item(sessao, slug) -> Item:
    return sessao.scalars(select(Item).where(Item.slug == slug)).one()


def test_carrega_os_47_itens_do_plano(catalogo):
    assert catalogo.scalar(select(func.count()).select_from(Item)) == 47


def test_itens_de_seguranca_marcados(catalogo):
    slugs = set(catalogo.scalars(select(Item.slug).where(Item.e_seguranca)).all())
    assert slugs == ITENS_DE_SEGURANCA


def test_body_tem_tamanhos_variantes_e_fases(catalogo):
    body = _item(catalogo, "body")

    assert {t.tamanho: t.quantidade_base for t in body.tamanhos} == {
        Tamanho.RN: 4, Tamanho.P: 8, Tamanho.M: 7, Tamanho.G: 6, Tamanho.GG: 6,
    }
    assert body.uso_clima == UsoClima.DIVIDE
    assert (body.variante_frio, body.variante_calor) == ("manga longa", "manga curta")
    assert body.escala_lavagem is True
    fases = {t.tamanho: t.fase_compra.codigo for t in body.tamanhos}
    assert fases[Tamanho.P] == "gestacao_7_8m"
    assert fases[Tamanho.GG] == "bebe_6_9m"


def test_regras_do_plano(catalogo):
    conforto = _item(catalogo, "bebe-conforto")
    regras = {(r.condicao, r.efeito): r.valor for r in conforto.regras}
    assert regras[(Condicao.SEM_CARRO, Efeito.MUDAR_PRIORIDADE)] == Prioridade.UTIL.value

    portao = _item(catalogo, "portao-seguranca")
    assert [(r.condicao, r.efeito) for r in portao.regras] == [
        (Condicao.CASA_COM_ESCADA, Efeito.INCLUIR_SO_SE)
    ]

    mosquiteiro = _item(catalogo, "mosquiteiro")
    assert (Condicao.PERFIL_QUENTE, Efeito.INCLUIR_SO_SE) in {
        (r.condicao, r.efeito) for r in mosquiteiro.regras
    }


def test_marcas_ligadas_com_faixa_e_nao_validadas(catalogo):
    berco = _item(catalogo, "berco")
    assert [v.marca.nome for v in berco.marcas][:2] == ["Tcil", "Reller"]
    assert all(v.faixa in Faixa for v in berco.marcas)
    assert catalogo.scalar(select(func.count()).select_from(Marca).where(Marca.validado)) == 0


def test_segunda_carga_nao_duplica_nem_sobrescreve(catalogo):
    berco = _item(catalogo, "berco")
    berco.nome = "Berço (editado no admin)"
    catalogo.flush()

    resumo = carregar_itens(catalogo)

    assert set(resumo.values()) == {0}
    assert _item(catalogo, "berco").nome == "Berço (editado no admin)"


def test_erro_de_digitacao_no_yaml_nomeia_o_item(sessao):
    carregar_base(sessao)
    carregar_marcas(sessao)
    dados = {
        "itens": [
            {
                "slug": "teste", "nome": "Teste", "categoria": "roupas",
                "fase": "gestacao_7_8m", "prioridade": "essencal",
                "quantidade": 1, "para_que_serve": "x", "como_escolher": "y",
            }
        ]
    }
    with pytest.raises(ValueError, match="item 'teste'.*essencal"):
        carregar_itens(sessao, dados)


def test_marca_desconhecida_e_recusada(sessao):
    carregar_base(sessao)
    carregar_marcas(sessao)
    dados = {
        "itens": [
            {
                "slug": "teste", "nome": "Teste", "categoria": "roupas",
                "fase": "gestacao_7_8m", "prioridade": "util", "quantidade": 1,
                "para_que_serve": "x", "como_escolher": "y", "marcas": ["Inexistente"],
            }
        ]
    }
    with pytest.raises(ValueError, match="item 'teste': marca 'Inexistente'"):
        carregar_itens(sessao, dados)


def test_item_sem_tamanhos_nem_quantidade_e_recusado(sessao):
    carregar_base(sessao)
    dados = {
        "itens": [
            {
                "slug": "teste", "nome": "Teste", "categoria": "roupas",
                "fase": "gestacao_7_8m", "prioridade": "util",
                "para_que_serve": "x", "como_escolher": "y",
            }
        ]
    }
    with pytest.raises(ValueError, match="item 'teste': informe 'tamanhos' ou 'quantidade'"):
        carregar_itens(sessao, dados)


def _item_basico(**extra):
    item = {
        "slug": "teste", "nome": "Teste", "categoria": "roupas",
        "fase": "gestacao_7_8m", "prioridade": "util", "quantidade": 1,
        "para_que_serve": "x", "como_escolher": "y",
    }
    item.update(extra)
    return {"itens": [item]}


def test_campo_obrigatorio_ausente_nomeia_o_item(sessao):
    carregar_base(sessao)
    dados = _item_basico()
    del dados["itens"][0]["prioridade"]

    with pytest.raises(ValueError, match="item 'teste'.*obrigatório.*prioridade"):
        carregar_itens(sessao, dados)


def test_campo_desconhecido_e_recusado(sessao):
    carregar_base(sessao)

    with pytest.raises(ValueError, match="item 'teste'.*desconhecido.*segurança"):
        carregar_itens(sessao, _item_basico(**{"segurança": True}))


def test_fase_de_tamanho_sem_o_tamanho_correspondente_e_recusada(sessao):
    carregar_base(sessao)
    dados = _item_basico(tamanhos={"P": 2}, fases_tamanho={"M": "bebe_0_3m"})
    del dados["itens"][0]["quantidade"]

    with pytest.raises(ValueError, match="item 'teste'.*fases_tamanho.*M"):
        carregar_itens(sessao, dados)
