"""Motor de montagem do enxoval: orquestra o cálculo da lista personalizada.

Este módulo é o ponto de entrada principal do motor de cálculo. Recebe as
respostas da família e o catálogo de itens (ambos como dataclasses imutáveis),
e produz um ``EnxovalCalculado`` com todas as linhas, fichas, roteiro e alertas.

**Regras de isolamento:**
- Não importa SQLAlchemy, FastAPI nem Pydantic.
- Não chama ``date.today()`` — recebe ``hoje`` como parâmetro.
- Funções com prefixo ``_`` são privadas ao módulo.
"""
from collections import defaultdict
from dataclasses import replace
from datetime import date
from fractions import Fraction

from app.db.enums import MomentoCompra, Tamanho, UsoClima
from app.motor.calendario import alertas_por_idade, montar_roteiro
from app.motor.clima import proporcao_frio
from app.motor.quantidades import dividir_variantes, fator_lavagem, quantidade
from app.motor.regras import Avaliacao, avaliar_regras, marcas_para
from app.motor.tipos import (
    Catalogo,
    EnxovalCalculado,
    FaseCalculada,
    Ficha,
    ItemCatalogo,
    JanelaTamanho,
    LinhaCalculada,
    Respostas,
    Resumo,
)

LIMITE_VOLUME_PADRAO = 40
DIAS_PRIMEIRO_ANO = 365
ORDEM_TAMANHOS = {tamanho: posicao for posicao, tamanho in enumerate(Tamanho)}


def _momento_compra(
    fase_codigo: str,
    roteiro: tuple[FaseCalculada, ...],
) -> MomentoCompra:
    """Calcula o momento de compra de um item com base na fase atual do roteiro."""
    # O roteiro está ordenado cronologicamente; usamos o índice como proxy de ordem
    indices = {f.codigo: i for i, f in enumerate(roteiro)}
    idx_atual = next((i for i, f in enumerate(roteiro) if f.atual), None)
    idx_linha = indices.get(fase_codigo)

    if idx_linha is None or idx_atual is None:
        return MomentoCompra.FUTURO

    diff = idx_linha - idx_atual
    if diff < 0:
        return MomentoCompra.ATRASADO
    if diff == 0:
        return MomentoCompra.AGORA
    if diff == 1:
        return MomentoCompra.PROXIMA_FASE
    return MomentoCompra.FUTURO


def montar_enxoval(
    respostas: Respostas,
    catalogo: Catalogo,
    hoje: date,
    limite_volume: int = LIMITE_VOLUME_PADRAO,
) -> EnxovalCalculado:
    fator = fator_lavagem(respostas.dias_entre_lavagens)
    janelas = {j.tamanho: j for j in catalogo.janelas}
    ordem_categoria = {c.slug: c.ordem for c in catalogo.categorias}
    avisos: list[str] = []
    linhas: list[LinhaCalculada] = []
    fichas: list[Ficha] = []

    # Roteiro calculado antes das linhas para poder classificar momento_compra
    roteiro = montar_roteiro(catalogo.fases, respostas.data_prevista, hoje)

    itens = sorted(
        catalogo.itens, key=lambda i: (ordem_categoria.get(i.categoria_slug, 10**6), i.ordem)
    )
    for item in itens:
        avaliacao = avaliar_regras(item, respostas)
        if not avaliacao.incluir:
            continue
        novas = _linhas_do_item(item, avaliacao, respostas, janelas, fator, avisos, roteiro)
        if not novas:
            continue
        linhas.extend(novas)
        avisos.extend(avaliacao.avisos)
        marcas = marcas_para(item.marcas, respostas.orcamento)
        fichas.append(
            Ficha(
                slug=item.slug,
                nome=item.nome,
                para_que_serve=item.para_que_serve,
                como_escolher=item.como_escolher,
                idade_inicio_meses=item.idade_inicio_meses,
                marcas=marcas,
                dicas=avaliacao.dicas,
                regras_seguranca=item.regras_seguranca,
            )
        )

    # O alerta continua inteiro; só os links para itens fora deste enxoval são removidos.
    presentes = {f.slug for f in fichas}
    alertas = tuple(
        replace(a, itens=tuple(i for i in a.itens if i in presentes))
        for a in alertas_por_idade(catalogo.regras_seguranca, respostas.data_prevista)
    )
    return EnxovalCalculado(
        linhas=tuple(linhas),
        fichas=tuple(fichas),
        roteiro=roteiro,
        alertas=alertas,
        resumo=_resumir(linhas, respostas, limite_volume),
        avisos=tuple(avisos),
    )


def _linhas_do_item(
    item: ItemCatalogo,
    avaliacao: Avaliacao,
    respostas: Respostas,
    janelas: dict[Tamanho, JanelaTamanho],
    fator: Fraction,
    avisos: list[str],
    roteiro: tuple[FaseCalculada, ...],
) -> list[LinhaCalculada]:
    escala = fator if item.escala_lavagem else Fraction(1)
    if item.tamanhos:
        saida: list[LinhaCalculada] = []
        for tamanho in sorted(item.tamanhos, key=lambda t: ORDEM_TAMANHOS[t.tamanho]):
            janela = janelas.get(tamanho.tamanho)
            if janela is None:
                avisos.append(
                    f"item '{item.slug}': sem janela de tamanho {tamanho.tamanho.value}; "
                    "sem divisão de clima"
                )
            elif janela.fim_dias <= janela.inicio_dias:
                avisos.append(
                    f"item '{item.slug}': janela de tamanho {tamanho.tamanho.value} inválida "
                    f"(de {janela.inicio_dias} a {janela.fim_dias} dias); sem divisão de clima"
                )
                janela = None
            fase_codigo = tamanho.fase_codigo or item.fase_codigo
            saida += _por_clima(
                item,
                avaliacao,
                respostas,
                quantidade(tamanho.quantidade_base, escala),
                (janela.inicio_dias, janela.fim_dias) if janela else None,
                tamanho.tamanho,
                fase_codigo,
                _momento_compra(fase_codigo, roteiro),
            )
        return saida
    if item.quantidade is None:
        avisos.append(f"item '{item.slug}': sem tamanhos nem quantidade; ignorado")
        return []
    return _por_clima(
        item,
        avaliacao,
        respostas,
        quantidade(item.quantidade, escala),
        (0, DIAS_PRIMEIRO_ANO),
        None,
        item.fase_codigo,
        _momento_compra(item.fase_codigo, roteiro),
    )


def _por_clima(
    item: ItemCatalogo,
    avaliacao: Avaliacao,
    respostas: Respostas,
    total: int,
    intervalo: tuple[int, int] | None,
    tamanho: Tamanho | None,
    fase_codigo: str,
    momento: MomentoCompra,
) -> list[LinhaCalculada]:
    if total <= 0:
        return []

    def linha(variante: str, rotulo: str | None, qtd: int) -> LinhaCalculada:
        return LinhaCalculada(
            chave=f"{item.slug}:{tamanho.value if tamanho else ''}:{variante}",
            item_slug=item.slug,
            nome=item.nome,
            categoria_slug=item.categoria_slug,
            tamanho=tamanho,
            variante=variante,
            rotulo_variante=rotulo,
            quantidade=qtd,
            unidade_texto=item.unidade_texto,
            prioridade=avaliacao.prioridade,
            fase_codigo=fase_codigo,
            e_seguranca=item.e_seguranca,
            escala_lavagem=item.escala_lavagem,
            momento_compra=momento,
        )

    if item.uso_clima == UsoClima.NEUTRO or (
        intervalo is None and item.uso_clima == UsoClima.DIVIDE
    ):
        return [linha("", None, total)]

    inicio, fim = intervalo or (0, DIAS_PRIMEIRO_ANO)
    data = respostas.data_prevista
    if item.uso_clima == UsoClima.SO_FRIO:
        tem_frio = proporcao_frio(data, inicio, fim, respostas.perfil, incluir_frescos=False) > 0
        return [linha("", None, total)] if tem_frio else []

    frio, calor = dividir_variantes(total, proporcao_frio(data, inicio, fim, respostas.perfil))
    saida = []
    if frio:
        saida.append(linha("frio", item.variante_frio, frio))
    if calor:
        saida.append(linha("calor", item.variante_calor, calor))
    return saida


def _resumir(linhas: list[LinhaCalculada], respostas: Respostas, limite_volume: int) -> Resumo:
    por_tamanho: dict[Tamanho, int] = defaultdict(int)
    for linha in linhas:
        if linha.tamanho is not None:
            por_tamanho[linha.tamanho] += linha.quantidade
    return Resumo(
        dias_sem_lavar=respostas.dias_entre_lavagens,
        total_unidades=sum(l.quantidade for l in linhas),
        aviso_volume_alto=max(por_tamanho.values(), default=0) > limite_volume,
        destacar_ja_tinha=not respostas.primeiro_filho,
    )
