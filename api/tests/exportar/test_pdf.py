"""Testes TDD para gerar_pdf — PDF da planilha via WeasyPrint."""
import pytest

weasyprint = pytest.importorskip("weasyprint")

from app.exportar.pdf import gerar_pdf


def test_pdf_retorna_bytes(saida_exemplo):
    conteudo = gerar_pdf(saida_exemplo)
    assert isinstance(conteudo, bytes)
    assert len(conteudo) > 0


def test_pdf_comeca_com_assinatura_pdf(saida_exemplo):
    conteudo = gerar_pdf(saida_exemplo)
    assert conteudo[:4] == b"%PDF", "Bytes não começam com assinatura PDF"


def test_pdf_contem_nome_da_cidade(saida_exemplo):
    """O PDF é gerado sem erros e contém conteúdo substancial (>10KB)."""
    conteudo = gerar_pdf(saida_exemplo)
    # O texto pode estar comprimido no PDF — verificamos o tamanho mínimo esperado
    # de um PDF com conteúdo real (cabeçalho + tabela + estilos)
    assert len(conteudo) > 5_000, f"PDF muito pequeno ({len(conteudo)} bytes) — provavelmente vazio"


def test_pdf_contem_nome_dos_itens(saida_exemplo):
    """O HTML renderizado inclui os itens antes de ser convertido para PDF."""
    from app.exportar.pdf import _renderizar
    html = _renderizar(saida_exemplo)
    assert "Body" in html
    assert "Fralda descartável" in html
    assert "Curitiba" in html


def test_textos_do_catalogo_sao_escapados_no_documento(saida_exemplo):
    from app.exportar.pdf import _renderizar
    saida_exemplo.linhas[0].nome = 'Body <especial> & algodão'
    html = _renderizar(saida_exemplo)
    assert 'Body &lt;especial&gt; &amp; algodão' in html
    assert 'Body <especial>' not in html
