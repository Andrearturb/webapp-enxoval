import pytest

from seed.base import carregar_base
from seed.itens import carregar_itens, carregar_marcas
from seed.seguranca import carregar_seguranca


def _regra(**extra):
    regra = {
        "codigo": "teste", "tema": "sono", "idade_inicio_meses": 0,
        "idade_fim_meses": 12, "texto": "x", "base": "SBP",
    }
    regra.update(extra)
    return [regra]


@pytest.fixture
def catalogo(sessao):
    carregar_base(sessao)
    carregar_marcas(sessao)
    carregar_itens(sessao)
    return sessao


def test_campo_desconhecido_na_regra_de_seguranca_e_recusado(catalogo):
    with pytest.raises(ValueError, match="regra 'teste'.*desconhecido.*iten"):
        carregar_seguranca(catalogo, _regra(iten=["berco"]))


def test_campo_obrigatorio_ausente_na_regra_de_seguranca(catalogo):
    dados = _regra()
    del dados[0]["texto"]

    with pytest.raises(ValueError, match="regra 'teste'.*obrigatório.*texto"):
        carregar_seguranca(catalogo, dados)
