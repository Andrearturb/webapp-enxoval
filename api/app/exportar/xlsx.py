"""Gerador de XLSX da planilha do enxoval.

Produz um arquivo Excel com duas abas:
- **Planilha**: itens agrupados por categoria, com formatação condicional
  para destacar linhas com itens faltando (fundo salmão).
- **Roteiro**: fases do roteiro de compras com datas e indicação da fase atual.

Utiliza ``openpyxl`` para geração e ``exportar.rotulos`` para os rótulos
legíveis de prioridade e momento de compra.
"""
import io

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app.exportar.rotulos import MOMENTO_COMPRA, PRIORIDADE
from app.rotas.schemas import EnxovalSaida

# ---------------------------------------------------------------------------
# Paleta de cores (ARGB sem "#") — tokens do design system
# ---------------------------------------------------------------------------
_COR_CABECALHO_FUNDO = "FF4F6B57"   # bg-principal  (verde-sálvia escuro)
_COR_CABECALHO_FONTE = "FFFFFFFF"   # branco
_COR_CATEGORIA_FUNDO = "FFEEF1EA"   # bg-principal-suave
_COR_CATEGORIA_FONTE = "FF2F3A33"   # text-texto
_COR_FALTANDO_FUNDO  = "FFF7E4DF"   # bg-alerta-fundo (salmão claro)


def _fill(cor: str) -> PatternFill:
    """Cria um ``PatternFill`` de preenchimento sólido com a cor ARGB informada."""
    return PatternFill("solid", fgColor=cor)


def _ajustar_larguras(ws) -> None:
    """Ajusta a largura de cada coluna com base no conteúdo máximo de cada célula."""
    for col in ws.columns:
        largura = max((len(str(cell.value or "")) for cell in col), default=8)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(largura + 4, 40)


def _aba_planilha(wb: Workbook, saida: EnxovalSaida) -> None:
    """Cria a aba 'Planilha' no workbook com cabeçalho, subtítulos de categoria e itens.

    Args:
        wb: Workbook openpyxl onde a aba será inserida.
        saida: Enxoval completo com linhas e categorias.
    """
    ws = wb.create_sheet("Planilha")

    # Cabeçalho fixo
    cabecalhos = [
        "Item", "Tamanho", "Quantidade", "Prioridade",
        "Momento", "Comprada", "Ganhada", "Já tinha", "Faltam",
    ]
    for col, titulo in enumerate(cabecalhos, start=1):
        cell = ws.cell(row=1, column=col, value=titulo)
        cell.font = Font(bold=True, color=_COR_CABECALHO_FONTE)
        cell.fill = _fill(_COR_CABECALHO_FUNDO)
        cell.alignment = Alignment(horizontal="center")

    ws.freeze_panes = "A2"
    linha_atual = 2

    for categoria in sorted(saida.categorias, key=lambda c: c.ordem):
        linhas_da_cat = [l for l in saida.linhas if l.categoria_slug == categoria.slug]
        if not linhas_da_cat:
            continue

        # Linha de subtítulo da categoria (mesclada)
        cell_cat = ws.cell(row=linha_atual, column=1, value=categoria.nome)
        cell_cat.font = Font(bold=True, color=_COR_CATEGORIA_FONTE)
        cell_cat.fill = _fill(_COR_CATEGORIA_FUNDO)
        ws.merge_cells(
            start_row=linha_atual, start_column=1,
            end_row=linha_atual, end_column=len(cabecalhos),
        )
        linha_atual += 1

        for linha in sorted(linhas_da_cat, key=lambda l: (l.nome, l.tamanho or "")):
            nome = linha.nome + (f" ({linha.rotulo_variante})" if linha.rotulo_variante else "")
            valores = [
                nome,
                linha.tamanho or "",
                linha.quantidade,
                PRIORIDADE.get(linha.prioridade, linha.prioridade),
                MOMENTO_COMPRA.get(linha.momento_compra, linha.momento_compra),
                linha.comprada,
                linha.ganhada,
                linha.ja_tinha,
                linha.faltam,
            ]
            for col, valor in enumerate(valores, start=1):
                cell = ws.cell(row=linha_atual, column=col, value=valor)
                if linha.faltam > 0:
                    cell.fill = _fill(_COR_FALTANDO_FUNDO)
            linha_atual += 1

    _ajustar_larguras(ws)


def _aba_roteiro(wb: Workbook, saida: EnxovalSaida) -> None:
    """Cria a aba 'Roteiro' no workbook com as fases do roteiro de compras.

    A fase atual é indicada com '✓' em negrito.

    Args:
        wb: Workbook openpyxl onde a aba será inserida.
        saida: Enxoval completo com roteiro de fases.
    """
    ws = wb.create_sheet("Roteiro")

    for col, titulo in enumerate(["Fase", "Início", "Fim", "Atual"], start=1):
        cell = ws.cell(row=1, column=col, value=titulo)
        cell.font = Font(bold=True, color=_COR_CABECALHO_FONTE)
        cell.fill = _fill(_COR_CABECALHO_FUNDO)

    for row, fase in enumerate(saida.roteiro, start=2):
        ws.cell(row=row, column=1, value=fase.nome)
        ws.cell(row=row, column=2, value=fase.inicio.strftime("%d/%m/%Y"))
        ws.cell(row=row, column=3, value=fase.fim.strftime("%d/%m/%Y"))
        atual_cell = ws.cell(row=row, column=4, value="✓" if fase.atual else "")
        if fase.atual:
            atual_cell.font = Font(bold=True, color=_COR_CABECALHO_FUNDO)

    _ajustar_larguras(ws)


def gerar_xlsx(saida: EnxovalSaida) -> bytes:
    """Gera o arquivo XLSX completo e retorna os bytes.

    Cria um workbook com as abas 'Planilha' e 'Roteiro', remove a aba
    padrão criada pelo openpyxl e serializa em memória.

    Args:
        saida: Enxoval completo com linhas, categorias e roteiro.

    Returns:
        Bytes do arquivo XLSX (assinatura ZIP ``PK``).
    """
    wb = Workbook()
    del wb[wb.sheetnames[0]]  # remove a aba vazia padrão

    _aba_planilha(wb, saida)
    _aba_roteiro(wb, saida)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
