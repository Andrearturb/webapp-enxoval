from dataclasses import replace

from app.db.enums import Condicao, Efeito, Faixa, Moradia, Prioridade
from app.motor.regras import avaliar_regras, condicao_vale, marcas_para
from app.motor.tipos import ItemCatalogo, MarcaDoItem, RegraItem

BASE = ItemCatalogo(
    slug="x", nome="X", categoria_slug="c", fase_codigo="f", ordem=1,
    para_que_serve="a", como_escolher="b", prioridade_base=Prioridade.ESSENCIAL, quantidade=1,
)


def _item(*regras, **extra) -> ItemCatalogo:
    return replace(BASE, regras=tuple(regras), **extra)


def test_item_sem_regras_entra_com_a_prioridade_base(fazer_respostas):
    avaliacao = avaliar_regras(_item(), fazer_respostas())

    assert avaliacao.incluir is True
    assert avaliacao.prioridade == Prioridade.ESSENCIAL
    assert avaliacao.dicas == ()


def test_incluir_so_se_depende_da_moradia(fazer_respostas):
    portao = _item(RegraItem(Condicao.CASA_COM_ESCADA, Efeito.INCLUIR_SO_SE))

    assert avaliar_regras(portao, fazer_respostas(moradia=Moradia.APARTAMENTO)).incluir is False
    assert avaliar_regras(portao, fazer_respostas(moradia=Moradia.CASA_SEM_ESCADA)).incluir is False
    assert avaliar_regras(portao, fazer_respostas(moradia=Moradia.CASA_COM_ESCADA)).incluir is True


def test_incluir_so_se_depende_do_clima(fazer_respostas):
    mosquiteiro = _item(RegraItem(Condicao.PERFIL_QUENTE, Efeito.INCLUIR_SO_SE))

    assert avaliar_regras(mosquiteiro, fazer_respostas(perfil="quente")).incluir is True
    assert avaliar_regras(mosquiteiro, fazer_respostas(perfil="frio")).incluir is False


def test_varias_regras_incluir_so_se_valem_como_ou(fazer_respostas):
    item = _item(
        RegraItem(Condicao.PERFIL_QUENTE, Efeito.INCLUIR_SO_SE),
        RegraItem(Condicao.PERFIL_MODERADO, Efeito.INCLUIR_SO_SE),
    )

    assert avaliar_regras(item, fazer_respostas(perfil="moderado")).incluir is True
    assert avaliar_regras(item, fazer_respostas(perfil="frio")).incluir is False


def test_mudar_prioridade_so_quando_a_condicao_vale(fazer_respostas):
    conforto = _item(RegraItem(Condicao.SEM_CARRO, Efeito.MUDAR_PRIORIDADE, "util"))

    assert avaliar_regras(conforto, fazer_respostas(carro=True)).prioridade == Prioridade.ESSENCIAL
    assert avaliar_regras(conforto, fazer_respostas(carro=False)).prioridade == Prioridade.UTIL


def test_dica_aparece_so_quando_a_condicao_vale(fazer_respostas):
    item = _item(RegraItem(Condicao.APARTAMENTO, Efeito.DICA, "Escolha um modelo compacto."))

    assert avaliar_regras(item, fazer_respostas(moradia=Moradia.APARTAMENTO)).dicas == (
        "Escolha um modelo compacto.",
    )
    assert avaliar_regras(item, fazer_respostas(moradia=Moradia.CASA_SEM_ESCADA)).dicas == ()


def test_item_de_seguranca_sem_regra_fisica_entra_em_qualquer_combinacao(fazer_respostas):
    berco = _item(e_seguranca=True)

    for orcamento in Faixa:
        for primeiro_filho in (True, False):
            respostas = fazer_respostas(orcamento=orcamento, primeiro_filho=primeiro_filho)
            assert avaliar_regras(berco, respostas).incluir is True


def test_condicao_vale_cobre_todas_as_condicoes(fazer_respostas):
    respostas = fazer_respostas(perfil="moderado", moradia=Moradia.CASA_COM_ESCADA, carro=False)

    esperado = {
        Condicao.COM_CARRO: False,
        Condicao.SEM_CARRO: True,
        Condicao.APARTAMENTO: False,
        Condicao.CASA_SEM_ESCADA: False,
        Condicao.CASA_COM_ESCADA: True,
        Condicao.PERFIL_QUENTE: False,
        Condicao.PERFIL_MODERADO: True,
        Condicao.PERFIL_FRIO: False,
    }
    assert {c: condicao_vale(c, respostas) for c in Condicao} == esperado


MARCAS = (
    MarcaDoItem("Barata 1", Faixa.ECONOMICO, 1),
    MarcaDoItem("Meio 1", Faixa.INTERMEDIARIO, 2),
    MarcaDoItem("Barata 2", Faixa.ECONOMICO, 3),
    MarcaDoItem("Cara 1", Faixa.INVESTIR, 4),
)


def test_marcas_da_faixa_pedida_na_ordem_do_catalogo():
    escolhidas = marcas_para(MARCAS, Faixa.ECONOMICO)

    assert escolhidas.nomes == ("Barata 1", "Barata 2")
    assert escolhidas.faixa == Faixa.ECONOMICO
    assert escolhidas.fallback is False


def test_faixa_sem_marcas_usa_a_vizinha_mais_barata_em_caso_de_empate():
    so_extremos = (MarcaDoItem("Barata", Faixa.ECONOMICO, 1), MarcaDoItem("Cara", Faixa.INVESTIR, 2))

    escolhidas = marcas_para(so_extremos, Faixa.INTERMEDIARIO)

    assert escolhidas.nomes == ("Barata",)
    assert escolhidas.faixa == Faixa.ECONOMICO
    assert escolhidas.fallback is True


def test_faixa_sem_marcas_anda_para_a_mais_proxima():
    so_caras = (MarcaDoItem("Cara", Faixa.INVESTIR, 1),)

    escolhidas = marcas_para(so_caras, Faixa.ECONOMICO)

    assert escolhidas.nomes == ("Cara",)
    assert escolhidas.faixa == Faixa.INVESTIR
    assert escolhidas.fallback is True


def test_item_sem_nenhuma_marca():
    escolhidas = marcas_para((), Faixa.INTERMEDIARIO)

    assert escolhidas.nomes == ()
    assert escolhidas.faixa is None
    assert escolhidas.fallback is False
