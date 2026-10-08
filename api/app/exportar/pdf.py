"""Gerador de PDF da planilha do enxoval via WeasyPrint + Jinja2.

Utiliza um template HTML em ``template.html`` renderizado pelo Jinja2
antes de ser convertido para PDF pelo WeasyPrint. Essa abordagem é mais
robusta do que substituições manuais de string e permite lógica condicional
real no template (``{% if %}``, ``{% for %}``, filtros, etc.).
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass
from datetime import date

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.exportar.rotulos import PRIORIDADE
from app.rotas.schemas import EnxovalSaida

# Diretório deste módulo — onde template.html reside
_TEMPLATE_DIR = pathlib.Path(__file__).parent

# Textos do catálogo são escapados antes de entrar no documento.
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(enabled_extensions=("html",)),
)


# ---------------------------------------------------------------------------
# Dataclasses de contexto do template
# ---------------------------------------------------------------------------


@dataclass
class _LinhaContexto:
    """Dados de uma linha prontos para o template Jinja2."""

    nome: str
    rotulo_variante: str | None
    tamanho: str | None
    quantidade: int
    prioridade: str           # valor do enum, ex.: "essencial"
    rotulo_prioridade: str    # rótulo legível, ex.: "Essencial"
    comprada: int
    ganhada: int
    ja_tinha: int
    faltam: int


@dataclass
class _CategoriaContexto:
    """Dados de uma categoria com suas linhas prontos para o template Jinja2."""

    nome: str
    linhas: list[_LinhaContexto]


# ---------------------------------------------------------------------------
# Funções internas
# ---------------------------------------------------------------------------


def _construir_contexto(saida: EnxovalSaida, hoje: date) -> dict:
    """Constrói o dicionário de contexto para o template Jinja2.

    Args:
        saida: Enxoval completo com linhas, categorias e progresso.
        hoje: Data de geração do documento.

    Returns:
        Dicionário com todas as variáveis usadas pelo template.
    """
    cidade = f"{saida.respostas.municipio.nome} – {saida.respostas.municipio.uf}"
    data_prevista = saida.respostas.data_prevista.strftime("%d/%m/%Y")
    gerado_em = hoje.strftime("%d/%m/%Y")

    categorias: list[_CategoriaContexto] = []
    for cat in sorted(saida.categorias, key=lambda c: c.ordem):
        linhas_da_cat = sorted(
            (l for l in saida.linhas if l.categoria_slug == cat.slug),
            key=lambda l: (l.nome, l.tamanho or ""),
        )
        if not linhas_da_cat:
            continue
        categorias.append(
            _CategoriaContexto(
                nome=cat.nome,
                linhas=[
                    _LinhaContexto(
                        nome=l.nome,
                        rotulo_variante=l.rotulo_variante,
                        tamanho=l.tamanho,
                        quantidade=l.quantidade,
                        prioridade=l.prioridade,
                        rotulo_prioridade=PRIORIDADE.get(l.prioridade, l.prioridade),
                        comprada=l.comprada,
                        ganhada=l.ganhada,
                        ja_tinha=l.ja_tinha,
                        faltam=l.faltam,
                    )
                    for l in linhas_da_cat
                ],
            )
        )

    return {
        "id_curto": str(saida.id)[:8].upper(),
        "cidade": cidade,
        "data_prevista": data_prevista,
        "gerado_em": gerado_em,
        "percentual": saida.progresso.percentual,
        "atendidas": saida.progresso.atendidas,
        "total": saida.progresso.total_unidades,
        "faltam": saida.progresso.faltam,
        "categorias": categorias,
    }


def _renderizar(saida: EnxovalSaida, hoje: date | None = None) -> str:
    """Renderiza o template HTML com Jinja2 e retorna a string HTML.

    Exposto para testes — permite verificar o conteúdo sem gerar o PDF.

    Args:
        saida: Enxoval completo.
        hoje: Data de geração; usa ``date.today()`` se omitida.

    Returns:
        String HTML pronta para ser convertida em PDF.
    """
    hoje = hoje or date.today()
    template = _jinja_env.get_template("template.html")
    return template.render(**_construir_contexto(saida, hoje))


def gerar_pdf(saida: EnxovalSaida, hoje: date | None = None) -> bytes:
    """Gera o PDF completo e retorna os bytes.

    Renderiza o template HTML via Jinja2 e converte para PDF com WeasyPrint.

    Args:
        saida: Enxoval completo com linhas, categorias e progresso.
        hoje: Data de geração; usa ``date.today()`` se omitida.

    Returns:
        Bytes do arquivo PDF (começa com ``%PDF``).
    """
    html_str = _renderizar(saida, hoje)
    return HTML(string=html_str, base_url=str(_TEMPLATE_DIR)).write_pdf()
