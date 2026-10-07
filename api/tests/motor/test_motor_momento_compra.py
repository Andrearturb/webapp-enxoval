"""Testes para a lógica de momento_compra calculada pelo motor.

Mapeamento DPP → fase atual com HOJE = 2027-02-01:
  DPP=2027-08-01  → gestacao_ate_5m
  DPP=2027-06-01  → gestacao_5_7m
  DPP=2027-04-01  → gestacao_7_8m
  DPP=2026-12-01  → bebe_0_3m
  DPP=2026-11-01  → bebe_3_6m
"""
from datetime import date

import pytest

from app.db.enums import MomentoCompra
from app.motor.montagem import montar_enxoval


HOJE = date(2027, 2, 1)

# DPPs que colocam HOJE em cada fase
DPP_ATE_5M = date(2027, 8, 1)
DPP_5_7M = date(2027, 6, 1)
DPP_7_8M = date(2027, 4, 1)
DPP_BEBE_0_3M = date(2026, 12, 1)
DPP_BEBE_3_6M = date(2026, 11, 1)


def _por_chave(enxoval) -> dict:
    return {l.chave: l for l in enxoval.linhas}


def _fase_atual(enxoval) -> str | None:
    f = next((f for f in enxoval.roteiro if f.atual), None)
    return f.codigo if f else None


def _momentos_do_item(enxoval, slug: str, tamanho: str | None = None) -> set:
    """Retorna o conjunto de momento_compra de um item (filtra tamanho se passado)."""
    linhas = [
        l for l in enxoval.linhas
        if l.item_slug == slug
        and (tamanho is None or (l.tamanho and l.tamanho.value == tamanho))
    ]
    assert linhas, f"Item '{slug}' (tamanho={tamanho}) não encontrado"
    return {l.momento_compra for l in linhas}


# ---------------------------------------------------------------------------
# gestacao_ate_5m — berço é proxima_fase, roupas RN são futuro
# ---------------------------------------------------------------------------

def test_gestacao_ate_5m_berco_e_proxima_fase(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(data_prevista=DPP_ATE_5M), catalogo, HOJE)
    assert _fase_atual(enxoval) == "gestacao_ate_5m"
    assert _momentos_do_item(enxoval, "berco") == {MomentoCompra.PROXIMA_FASE}


def test_gestacao_ate_5m_roupas_rn_sao_futuro(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(data_prevista=DPP_ATE_5M), catalogo, HOJE)
    # RN está na gestacao_7_8m, que é 2 fases à frente → futuro
    assert _momentos_do_item(enxoval, "body", tamanho="RN") == {MomentoCompra.FUTURO}


def test_gestacao_ate_5m_fraldas_sao_futuro(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(data_prevista=DPP_ATE_5M), catalogo, HOJE)
    linhas = _por_chave(enxoval)
    assert linhas["fraldas-descartaveis::"].momento_compra == MomentoCompra.FUTURO


# ---------------------------------------------------------------------------
# gestacao_5_7m — berço é agora, roupas RN são proxima_fase
# ---------------------------------------------------------------------------

def test_gestacao_5_7m_berco_e_agora(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(data_prevista=DPP_5_7M), catalogo, HOJE)
    assert _fase_atual(enxoval) == "gestacao_5_7m"
    linhas = _por_chave(enxoval)
    assert linhas["berco::"].momento_compra == MomentoCompra.AGORA
    assert linhas["carrinho::"].momento_compra == MomentoCompra.AGORA


def test_gestacao_5_7m_roupas_rn_sao_proxima_fase(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(data_prevista=DPP_5_7M), catalogo, HOJE)
    # RN está na gestacao_7_8m, que é 1 fase à frente → proxima_fase
    assert _momentos_do_item(enxoval, "body", tamanho="RN") == {MomentoCompra.PROXIMA_FASE}
    assert _momentos_do_item(enxoval, "macacao", tamanho="RN") == {MomentoCompra.PROXIMA_FASE}


# ---------------------------------------------------------------------------
# gestacao_7_8m — roupas RN são agora, berço é atrasado
# ---------------------------------------------------------------------------

def test_gestacao_7_8m_roupas_rn_sao_agora(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(data_prevista=DPP_7_8M), catalogo, HOJE)
    assert _fase_atual(enxoval) == "gestacao_7_8m"
    assert _momentos_do_item(enxoval, "body", tamanho="RN") == {MomentoCompra.AGORA}
    linhas = _por_chave(enxoval)
    assert linhas["fraldas-descartaveis::"].momento_compra == MomentoCompra.AGORA


def test_gestacao_7_8m_berco_e_atrasado(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(data_prevista=DPP_7_8M), catalogo, HOJE)
    linhas = _por_chave(enxoval)
    assert linhas["berco::"].momento_compra == MomentoCompra.ATRASADO
    assert linhas["carrinho::"].momento_compra == MomentoCompra.ATRASADO


# ---------------------------------------------------------------------------
# bebe_0_3m — berço e roupas RN são atrasados, roupas M são agora
# ---------------------------------------------------------------------------

def test_bebe_0_3m_berco_e_roupas_gestacao_sao_atrasados(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(data_prevista=DPP_BEBE_0_3M), catalogo, HOJE)
    assert _fase_atual(enxoval) == "bebe_0_3m"
    linhas = _por_chave(enxoval)
    assert linhas["berco::"].momento_compra == MomentoCompra.ATRASADO
    assert _momentos_do_item(enxoval, "body", tamanho="RN") == {MomentoCompra.ATRASADO}


def test_bebe_0_3m_roupas_M_sao_agora(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(data_prevista=DPP_BEBE_0_3M), catalogo, HOJE)
    # Tamanho M tem fase bebe_0_3m → agora
    assert MomentoCompra.AGORA in _momentos_do_item(enxoval, "body", tamanho="M")


def test_bebe_0_3m_cadeira_e_futuro_ou_proxima(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(data_prevista=DPP_BEBE_0_3M), catalogo, HOJE)
    linhas = _por_chave(enxoval)
    assert linhas["cadeira-alimentacao::"].momento_compra in (
        MomentoCompra.PROXIMA_FASE, MomentoCompra.FUTURO
    )


# ---------------------------------------------------------------------------
# Consistência: momento_compra em todas as linhas
# ---------------------------------------------------------------------------

def test_todas_as_linhas_tem_momento_compra_valido(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(), catalogo, HOJE)
    for linha in enxoval.linhas:
        assert isinstance(linha.momento_compra, MomentoCompra), (
            f"linha {linha.chave}: momento_compra inválido ({linha.momento_compra!r})"
        )
