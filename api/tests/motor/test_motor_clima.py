from datetime import date
from fractions import Fraction

import pytest

from app.db.enums import PerfilCodigo
from app.motor.clima import proporcao_frio, resolver_perfil
from app.motor.tipos import PerfilClima

FRIO = PerfilClima(PerfilCodigo.FRIO, frozenset({5, 6, 7, 8, 9}), frozenset())
QUENTE = PerfilClima(PerfilCodigo.QUENTE, frozenset(), frozenset({6, 7}))
JUNHO = date(2027, 6, 15)


def test_resolver_perfil_correcao_vence_excecao_que_vence_estado():
    assert resolver_perfil(PerfilCodigo.FRIO, PerfilCodigo.QUENTE, PerfilCodigo.MODERADO) == PerfilCodigo.MODERADO
    assert resolver_perfil(PerfilCodigo.FRIO, PerfilCodigo.QUENTE, None) == PerfilCodigo.FRIO
    assert resolver_perfil(None, PerfilCodigo.QUENTE, None) == PerfilCodigo.QUENTE


def test_janela_inteira_em_mes_frio_vale_um():
    # 15/jun a 12/set (dias 0 a 89): só meses 6, 7, 8 e 9
    assert proporcao_frio(JUNHO, 0, 90, FRIO) == 1


def test_janela_com_parte_em_mes_frio():
    # 13/set a 11/dez (dias 90 a 179): só 13 a 30/set (18 dias) são frios, de 90
    assert proporcao_frio(JUNHO, 90, 180, FRIO) == Fraction(1, 5)


def test_janela_sem_mes_frio_vale_zero():
    # 12/dez a 10/mar (dias 180 a 269)
    assert proporcao_frio(JUNHO, 180, 270, FRIO) == 0


def test_mes_fresco_vale_metade():
    # 15/jun a 12/set: junho (16 dias) + julho (31 dias) = 47 dias frescos, cada um vale 1/2
    assert proporcao_frio(JUNHO, 0, 90, QUENTE) == Fraction(47, 180)


def test_sem_contar_os_frescos_o_perfil_quente_nunca_tem_frio():
    assert proporcao_frio(JUNHO, 0, 90, QUENTE, incluir_frescos=False) == 0


def test_mes_que_e_frio_e_fresco_conta_como_frio():
    ambos = PerfilClima(PerfilCodigo.MODERADO, frozenset({6}), frozenset({6}))
    assert proporcao_frio(date(2027, 6, 1), 0, 30, ambos) == 1


def test_nascimento_em_dezembro_atravessa_a_virada_de_ano():
    inverno_do_hemisferio_errado = PerfilClima(PerfilCodigo.FRIO, frozenset({12, 1, 2}), frozenset())
    # 20/dez/2027 a 18/mar/2028 (2028 é bissexto): 12 + 31 + 29 = 72 dias frios de 90
    assert proporcao_frio(date(2027, 12, 20), 0, 90, inverno_do_hemisferio_errado) == Fraction(4, 5)


@pytest.mark.parametrize(("inicio", "fim"), [(10, 10), (10, 5)])
def test_janela_vazia_ou_invertida_e_recusada(inicio, fim):
    with pytest.raises(ValueError, match="janela"):
        proporcao_frio(JUNHO, inicio, fim, FRIO)
