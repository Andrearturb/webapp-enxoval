from datetime import date, timedelta

import pytest

from app.motor.calendario import (
    adicionar_meses,
    alertas_por_idade,
    intervalo_da_fase,
    montar_roteiro,
)

DPP = date(2027, 6, 15)


@pytest.mark.parametrize(
    ("origem", "meses", "esperado"),
    [
        (date(2027, 1, 31), 1, date(2027, 2, 28)),
        (date(2028, 1, 31), 1, date(2028, 2, 29)),  # ano bissexto
        (date(2028, 2, 29), 12, date(2029, 2, 28)),  # 29/fev + 1 ano
        (date(2026, 12, 15), 2, date(2027, 2, 15)),  # virada de ano
        (date(2027, 6, 15), 0, date(2027, 6, 15)),
        (date(2027, 6, 15), 12, date(2028, 6, 15)),
    ],
)
def test_adicionar_meses_ajusta_fim_de_mes(origem, meses, esperado):
    assert adicionar_meses(origem, meses) == esperado


def test_intervalo_de_fase_da_gestacao_conta_a_partir_de_dpp_menos_40_semanas(catalogo):
    fase = next(f for f in catalogo.fases if f.codigo == "gestacao_5_7m")  # semanas 18 a 26

    # início da gestação = 15/jun/2027 - 280 dias = 8/set/2026; semana 18 começa 126 dias depois
    assert intervalo_da_fase(fase, DPP) == (date(2027, 1, 12), date(2027, 3, 15))


def test_intervalo_de_fase_do_bebe_conta_meses_completos_depois_da_dpp(catalogo):
    fase = next(f for f in catalogo.fases if f.codigo == "bebe_0_3m")  # meses 0 a 2

    assert intervalo_da_fase(fase, DPP) == (date(2027, 6, 15), date(2027, 9, 14))


def test_fases_da_gestacao_sao_contiguas(catalogo):
    fases = [f for f in montar_roteiro(catalogo.fases, DPP, date(2027, 2, 1))][:4]

    for anterior, seguinte in zip(fases, fases[1:], strict=False):
        assert (seguinte.inicio - anterior.fim).days == 1


def test_fase_atual_e_a_que_contem_hoje(catalogo):
    roteiro = montar_roteiro(catalogo.fases, DPP, date(2027, 2, 1))

    atuais = [f.codigo for f in roteiro if f.atual]
    assert atuais == ["gestacao_5_7m"]
    assert len(roteiro) == 8


@pytest.mark.parametrize("hoje", [date(2026, 1, 1), date(2030, 1, 1)])
def test_hoje_fora_do_roteiro_nao_tem_fase_atual_e_nao_quebra(catalogo, hoje):
    roteiro = montar_roteiro(catalogo.fases, DPP, hoje)

    assert len(roteiro) == 8
    assert not any(f.atual for f in roteiro)


def test_roteiro_com_dpp_em_29_de_fevereiro(catalogo):
    roteiro = montar_roteiro(catalogo.fases, date(2028, 2, 29), date(2028, 3, 1))

    ultima = roteiro[-1]  # bebe_9_12m: meses 9 a 11
    assert ultima.inicio == date(2028, 11, 29)
    assert ultima.fim == date(2029, 2, 27)  # 29/fev/2028 + 12 meses = 28/fev/2029, menos 1 dia


def test_alertas_comecam_na_idade_certa_e_vem_em_ordem(catalogo):
    alertas = alertas_por_idade(catalogo.regras_seguranca, DPP)

    por_codigo = {a.codigo: a for a in alertas}
    assert len(alertas) == 8
    assert por_codigo["sono-seguro"].ativo_a_partir == date(2027, 6, 15)
    assert por_codigo["sono-seguro"].ativo_ate == date(2028, 6, 15)
    assert por_codigo["introducao-alimentar"].ativo_a_partir == date(2027, 12, 15)
    assert por_codigo["introducao-alimentar"].ativo_ate == date(2028, 3, 15)
    datas = [a.ativo_a_partir for a in alertas]
    assert datas == sorted(datas)
    assert "berco" in por_codigo["sono-seguro"].itens


def test_depois_da_data_prevista_a_fase_do_bebe_vence_a_reta_final(catalogo):
    """Com o bebê já previsto, 'conferir a mala e descansar' não pode ser o passo em destaque."""
    roteiro = montar_roteiro(catalogo.fases, DPP, date(2027, 6, 20))

    assert [f.codigo for f in roteiro if f.atual] == ["bebe_0_3m"]


def test_antes_da_data_prevista_a_sobreposicao_vale_a_primeira_fase(catalogo):
    from app.db.enums import ReferenciaFase
    from app.motor.tipos import Fase

    # duas fases de gestação que se sobrepõem de propósito
    fases = (
        Fase("a", "A", ReferenciaFase.GESTACAO_SEMANA, 10, 30, "t", 1),
        Fase("b", "B", ReferenciaFase.GESTACAO_SEMANA, 20, 39, "t", 2),
    )

    roteiro = montar_roteiro(fases, DPP, DPP - timedelta(weeks=15))

    assert [f.codigo for f in roteiro if f.atual] == ["a"]
