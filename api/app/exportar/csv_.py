"""Gerador de CSV da planilha do enxoval."""
import csv
import io

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

_ROTULO_PRIORIDADE = {
    "essencial": "Essencial",
    "util": "Útil",
    "pode_esperar": "Pode esperar",
}


def gerar_csv(saida: EnxovalSaida) -> str:
    """Devolve o CSV completo como string UTF-8 com BOM para abertura correta no Excel."""
    categorias_por_slug = {c.slug: c for c in saida.categorias}
    categorias_ordenadas = sorted(saida.categorias, key=lambda c: c.ordem)

    saida_buf = io.StringIO()
    writer = csv.DictWriter(
        saida_buf,
        fieldnames=_COLUNAS,
        lineterminator="\r\n",
    )
    writer.writeheader()

    for categoria in categorias_ordenadas:
        linhas_da_cat = [l for l in saida.linhas if l.categoria_slug == categoria.slug]
        linhas_da_cat.sort(key=lambda l: (l.nome, l.tamanho or ""))

        for linha in linhas_da_cat:
            writer.writerow({
                "Categoria": categoria.nome,
                "Item": linha.nome + (f" ({linha.rotulo_variante})" if linha.rotulo_variante else ""),
                "Tamanho": linha.tamanho or "",
                "Quantidade": linha.quantidade,
                "Prioridade": _ROTULO_PRIORIDADE.get(linha.prioridade, linha.prioridade),
                "Comprada": linha.comprada,
                "Ganhada": linha.ganhada,
                "Já tinha": linha.ja_tinha,
                "Faltam": linha.faltam,
            })

    # BOM UTF-8 garante que Excel abre com acentuação correta
    return "\ufeff" + saida_buf.getvalue()
