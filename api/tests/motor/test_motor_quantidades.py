from fractions import Fraction

import pytest

from app.motor.quantidades import dividir_variantes, fator_lavagem, quantidade


@pytest.mark.parametrize(
    ("dias", "esperado"),
    [(1, Fraction(2, 3)), (2, Fraction(1)), (3, Fraction(4, 3)), (4, Fraction(5, 3)), (7, Fraction(8, 3))],
)
def test_fator_lavagem(dias, esperado):
    assert fator_lavagem(dias) == esperado


@pytest.mark.parametrize("dias", [-1, 0, 8, 30])
def test_fator_fora_de_1_a_7_e_recusado(dias):
    with pytest.raises(ValueError, match="entre 1 e 7"):
        fator_lavagem(dias)


@pytest.mark.parametrize(
    ("base", "dias", "esperado"),
    [(8, 2, 8), (8, 3, 11), (8, 1, 6), (0, 3, 0), (1, 1, 1), (6, 4, 10)],
)
def test_quantidade_arredonda_para_cima(base, dias, esperado):
    assert quantidade(base, fator_lavagem(dias)) == esperado


def test_quantidade_base_negativa_e_recusada():
    with pytest.raises(ValueError, match="negativa"):
        quantidade(-1, Fraction(1))


def test_dividir_preserva_o_total_em_toda_a_grade():
    for total in range(0, 31):
        for numerador in range(0, 21):
            frio, calor = dividir_variantes(total, Fraction(numerador, 20))
            assert frio + calor == total
            assert 0 <= frio <= total


@pytest.mark.parametrize(
    ("total", "proporcao", "frio", "calor"),
    [
        (8, Fraction(0), 0, 8),
        (8, Fraction(1), 8, 0),
        (1, Fraction(1, 2), 1, 0),  # meio para cima, não para o par
        (3, Fraction(1, 2), 2, 1),
        (7, Fraction(1, 5), 1, 6),
        (8, Fraction(47, 180), 2, 6),
    ],
)
def test_dividir_variantes_meio_para_cima(total, proporcao, frio, calor):
    assert dividir_variantes(total, proporcao) == (frio, calor)


def test_dividir_recusa_proporcao_fora_de_0_a_1():
    with pytest.raises(ValueError, match="entre 0 e 1"):
        dividir_variantes(5, Fraction(3, 2))


def test_dividir_recusa_total_negativo():
    with pytest.raises(ValueError, match="negativa"):
        dividir_variantes(-1, Fraction(1, 2))
