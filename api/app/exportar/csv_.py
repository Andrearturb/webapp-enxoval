"""Gerador de CSV da planilha do enxoval.

Produz um arquivo CSV com BOM UTF-8 para abertura correta no Microsoft Excel,
com os itens agrupados por categoria em ordem de exibição.
"""
import csv
import io

from app.exportar.rotulos import PRIORIDADE
from app.rotas.schemas import EnxovalSaida

_COLUNAS = [
    "Categoria",
    "Item",
    "Tamanho",
    "Quantidade",
    "Prioridade",
    "Comprada",
    "Ganhada",
    "Já tinha",
    "Faltam",
]


def gerar_csv(saida: EnxovalSaida) -> str:
    """Gera o CSV completo como string UTF-8 com BOM.

    Os itens são ordenados por ``categoria.ordem`` e, dentro de cada categoria,
    por nome e tamanho. O BOM (``\\ufeff``) garante que o Excel abra o arquivo
    com acentuação correta sem precisar importar manualmente.

    Args:
        saida: Enxoval completo com linhas, categorias e progresso.

    Returns:
        String CSV com BOM UTF-8.
    """
    categorias_ordenadas = sorted(saida.categorias, key=lambda c: c.ordem)

    saida_buf = io.StringIO()
    writer = csv.DictWriter(
        saida_buf,
        fieldnames=_COLUNAS,
        lineterminator="\r\n",
    )
    writer.writeheader()

    for categoria in categorias_ordenadas:
        linhas_da_cat = sorted(
            (l for l in saida.linhas if l.categoria_slug == categoria.slug),
            key=lambda l: (l.nome, l.tamanho or ""),
        )
        for linha in linhas_da_cat:
            nome = linha.nome + (f" ({linha.rotulo_variante})" if linha.rotulo_variante else "")
            writer.writerow({
                "Categoria": categoria.nome,
                "Item": nome,
                "Tamanho": linha.tamanho or "",
                "Quantidade": linha.quantidade,
                "Prioridade": PRIORIDADE.get(linha.prioridade, linha.prioridade),
                "Comprada": linha.comprada,
                "Ganhada": linha.ganhada,
                "Já tinha": linha.ja_tinha,
                "Faltam": linha.faltam,
            })

    # BOM UTF-8 para compatibilidade com Excel
    return "\ufeff" + saida_buf.getvalue()
