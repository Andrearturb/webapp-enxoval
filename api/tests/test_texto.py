import pytest

from app.texto import normalizar_busca


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("São João d'Aliança", "sao joao d alianca"),
        ("Alta Floresta D'Oeste", "alta floresta d oeste"),
        ("Alta Floresta D’Oeste", "alta floresta d oeste"),  # apóstrofo tipográfico
        ("Olhos-d'Água", "olhos d agua"),
        ("Mogi-Mirim", "mogi mirim"),
        ("  Florianópolis ", "florianopolis"),
        ("SAO   PAULO", "sao paulo"),
        ("Içara", "icara"),
        ("Dona Inês", "dona ines"),
        ("", ""),
        ("---", ""),
    ],
)
def test_normalizar_busca(entrada, esperado):
    assert normalizar_busca(entrada) == esperado


def test_apostrofos_diferentes_dao_o_mesmo_resultado():
    assert normalizar_busca("D'Oeste") == normalizar_busca("D’Oeste")


def test_seed_usa_a_mesma_funcao():
    from seed.cidades import normalizar_busca as do_seed

    assert do_seed is normalizar_busca
