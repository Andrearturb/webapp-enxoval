"""Testes TDD para gerar_xlsx — planilha XLSX da planilha."""
import io

import pytest

openpyxl = pytest.importorskip("openpyxl")

from app.exportar.xlsx import gerar_xlsx


def _abrir(conteudo: bytes):
    return openpyxl.load_workbook(io.BytesIO(conteudo))


def test_xlsx_retorna_bytes(saida_exemplo):
    conteudo = gerar_xlsx(saida_exemplo)
    assert isinstance(conteudo, bytes)
    assert len(conteudo) > 0


def test_xlsx_tem_aba_planilha(saida_exemplo):
    wb = _abrir(gerar_xlsx(saida_exemplo))
    assert "Planilha" in wb.sheetnames


def test_xlsx_tem_aba_roteiro(saida_exemplo):
    wb = _abrir(gerar_xlsx(saida_exemplo))
    assert "Roteiro" in wb.sheetnames


def test_xlsx_planilha_tem_cabecalho(saida_exemplo):
    wb = _abrir(gerar_xlsx(saida_exemplo))
    ws = wb["Planilha"]
    # Primeira linha deve conter os cabeçalhos
    cabecalhos = [ws.cell(1, c).value for c in range(1, 10)]
    assert "Item" in cabecalhos
    assert "Quantidade" in cabecalhos
    assert "Faltam" in cabecalhos


def test_xlsx_planilha_contem_nomes_dos_itens(saida_exemplo):
    wb = _abrir(gerar_xlsx(saida_exemplo))
    ws = wb["Planilha"]
    valores = {ws.cell(r, c).value for r in range(1, ws.max_row + 1) for c in range(1, ws.max_column + 1)}
    assert "Body" in valores
    assert "Fralda descartável" in valores


def test_xlsx_planilha_contem_nomes_de_categorias(saida_exemplo):
    wb = _abrir(gerar_xlsx(saida_exemplo))
    ws = wb["Planilha"]
    valores = {ws.cell(r, 1).value for r in range(1, ws.max_row + 1)}
    assert "Roupas" in valores
    assert "Higiene" in valores


def test_xlsx_roteiro_contem_fases(saida_exemplo):
    wb = _abrir(gerar_xlsx(saida_exemplo))
    ws = wb["Roteiro"]
    valores = {ws.cell(r, c).value for r in range(1, ws.max_row + 1) for c in range(1, 4)}
    assert "7º–8º mês de gestação" in valores
    assert "0–3 meses" in valores


def test_xlsx_bytes_comecam_com_assinatura_zip(saida_exemplo):
    """Arquivos XLSX são ZIPs — verificar assinatura PK."""
    conteudo = gerar_xlsx(saida_exemplo)
    assert conteudo[:2] == b"PK", "XLSX deve começar com assinatura ZIP (PK)"
