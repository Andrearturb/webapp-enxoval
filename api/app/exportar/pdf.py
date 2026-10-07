"""Gerador de PDF da planilha do enxoval via WeasyPrint."""
from __future__ import annotations

import pathlib
from datetime import date, datetime

from weasyprint import HTML

from app.rotas.schemas import EnxovalSaida

_TEMPLATE = (pathlib.Path(__file__).parent / "template.html").read_text(encoding="utf-8")

_ROTULO_PRIORIDADE = {
    "essencial": "Essencial",
    "util": "Útil",
    "pode_esperar": "Pode esperar",
}


def _renderizar(saida: EnxovalSaida, hoje: date | None = None) -> str:
    """Substitui as variáveis do template HTML manualmente (sem Jinja2)."""
    hoje = hoje or date.today()

    cidade = f"{saida.respostas.municipio.nome} – {saida.respostas.municipio.uf}"
    data_prevista = saida.respostas.data_prevista.strftime("%d/%m/%Y")
    gerado_em = hoje.strftime("%d/%m/%Y")

    # Progresso
    html = _TEMPLATE.replace("{{ cidade }}", cidade)
    html = html.replace("{{ data_prevista }}", data_prevista)
    html = html.replace("{{ gerado_em }}", gerado_em)
    html = html.replace("{{ percentual }}", str(saida.progresso.percentual))
    html = html.replace("{{ atendidas }}", str(saida.progresso.atendidas))
    html = html.replace("{{ total }}", str(saida.progresso.total_unidades))
    html = html.replace("{{ faltam }}", str(saida.progresso.faltam))

    # Categorias e linhas
    cats_ordenadas = sorted(saida.categorias, key=lambda c: c.ordem)
    blocos_categorias = []
    for cat in cats_ordenadas:
        linhas_da_cat = [l for l in saida.linhas if l.categoria_slug == cat.slug]
        if not linhas_da_cat:
            continue
        linhas_da_cat.sort(key=lambda l: (l.nome, l.tamanho or ""))

        linhas_html = []
        for linha in linhas_da_cat:
            nome = linha.nome
            rotulo_variante = f" ({linha.rotulo_variante})" if linha.rotulo_variante else ""
            tamanho = linha.tamanho or ""
            prioridade_classe = linha.prioridade
            prioridade_rotulo = _ROTULO_PRIORIDADE.get(linha.prioridade, linha.prioridade)
            classe_tr = "faltando" if linha.faltam > 0 else ""
            classe_faltam = "faltam-positivo" if linha.faltam > 0 else "faltam-zero"

            linhas_html.append(f"""
      <tr class="{classe_tr}">
        <td>{nome}{rotulo_variante}</td>
        <td>{tamanho}</td>
        <td class="num-col">{linha.quantidade}</td>
        <td class="prioridade-{prioridade_classe}">{prioridade_rotulo}</td>
        <td class="num-col">{linha.comprada}</td>
        <td class="num-col">{linha.ganhada}</td>
        <td class="num-col">{linha.ja_tinha}</td>
        <td class="num-col {classe_faltam}">{linha.faltam}</td>
      </tr>""")

        blocos_categorias.append(f"""<div class="categoria">
  <h2>{cat.nome}</h2>
  <table>
    <thead>
      <tr>
        <th>Item</th>
        <th>Tam.</th>
        <th class="num-col">Qtd.</th>
        <th>Prioridade</th>
        <th class="num-col">Comprada</th>
        <th class="num-col">Ganhada</th>
        <th class="num-col">Já tinha</th>
        <th class="num-col">Faltam</th>
      </tr>
    </thead>
    <tbody>{"".join(linhas_html)}
    </tbody>
  </table>
</div>""")

    # Substituir o bloco {% for categoria in categorias %}...{% endfor %}
    inicio = html.find("{% for categoria in categorias %}")
    fim = html.find("{% endfor %}") + len("{% endfor %}")
    html = html[:inicio] + "\n".join(blocos_categorias) + html[fim:]

    return html


def gerar_pdf(saida: EnxovalSaida, hoje: date | None = None) -> bytes:
    """Devolve o PDF completo como bytes."""
    html_str = _renderizar(saida, hoje)
    return HTML(string=html_str).write_pdf()
