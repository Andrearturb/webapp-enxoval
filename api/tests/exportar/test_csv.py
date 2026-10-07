"""Testes TDD para gerar_csv — formato CSV da planilha."""
import csv
import io

import pytest

from app.exportar.csv_ import gerar_csv


def _linhas(conteudo: str) -> list[dict]:
    """Parseia o CSV e devolve lista de dicts (usando DictReader).
    Usa utf-8-sig para ignorar o BOM UTF-8 adicionado para compatibilidade com Excel.
    """
    # Remove BOM se presente antes de parsear
    sem_bom = conteudo.lstrip("\ufeff")
    return list(csv.DictReader(io.StringIO(sem_bom)))


def test_csv_tem_cabecalho_correto(saida_exemplo):
    conteudo = gerar_csv(saida_exemplo)
    linhas = _linhas(conteudo)
    assert linhas, "CSV vazio"
    colunas = set(linhas[0].keys())
    esperadas = {"Categoria", "Item", "Tamanho", "Quantidade", "Prioridade",
                 "Comprada", "Ganhada", "Já tinha", "Faltam"}
    assert esperadas.issubset(colunas), f"Colunas faltando: {esperadas - colunas}"


def test_csv_contem_todos_os_itens(saida_exemplo):
    conteudo = gerar_csv(saida_exemplo)
    linhas = _linhas(conteudo)
    nomes = [l["Item"] for l in linhas]
    assert "Body" in nomes
    assert "Macacão" in nomes
    assert "Fralda descartável" in nomes


def test_csv_quantidades_corretas(saida_exemplo):
    conteudo = gerar_csv(saida_exemplo)
    linhas = _linhas(conteudo)
    body = next(l for l in linhas if l["Item"] == "Body")
    assert body["Quantidade"] == "8"
    assert body["Comprada"] == "3"
    assert body["Faltam"] == "5"


def test_csv_itens_agrupados_por_categoria(saida_exemplo):
    conteudo = gerar_csv(saida_exemplo)
    linhas = _linhas(conteudo)
    categorias = [l["Categoria"] for l in linhas]
    # Todos os itens de "Roupas" devem vir antes de "Higiene" (ordem por categoria.ordem)
    idx_roupas = [i for i, c in enumerate(categorias) if c == "Roupas"]
    idx_higiene = [i for i, c in enumerate(categorias) if c == "Higiene"]
    assert idx_roupas, "Nenhum item de Roupas"
    assert idx_higiene, "Nenhum item de Higiene"
    assert max(idx_roupas) < min(idx_higiene), "Roupas deve preceder Higiene"


def test_csv_tamanho_vazio_para_itens_sem_tamanho(saida_exemplo):
    conteudo = gerar_csv(saida_exemplo)
    linhas = _linhas(conteudo)
    fralda = next(l for l in linhas if l["Item"] == "Fralda descartável")
    assert fralda["Tamanho"] == ""


def test_csv_retorna_string_utf8(saida_exemplo):
    conteudo = gerar_csv(saida_exemplo)
    assert isinstance(conteudo, str)
    # Deve conter caractere acentuado sem erro
    assert "Já tinha" in conteudo
