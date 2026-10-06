import calendar
from collections.abc import Iterable
from datetime import date, timedelta

from app.db.enums import ReferenciaFase
from app.motor.tipos import Alerta, Fase, FaseCalculada, RegraSegurancaCatalogo

SEMANAS_DE_GESTACAO = 40


def adicionar_meses(d: date, meses: int) -> date:
    """Soma meses de calendário; se o dia não existir no mês de destino, usa o último dia."""
    indice = d.month - 1 + meses
    ano = d.year + indice // 12
    mes = indice % 12 + 1
    dia = min(d.day, calendar.monthrange(ano, mes)[1])
    return date(ano, mes, dia)


def intervalo_da_fase(fase: Fase, data_prevista: date) -> tuple[date, date]:
    """Início e fim da fase, ambos inclusivos.

    Fases da gestação contam semanas desde (data prevista - 40 semanas); fases do bebê contam
    meses completos desde a data prevista (de `inicio` até o fim do mês `fim`).
    """
    if fase.referencia == ReferenciaFase.GESTACAO_SEMANA:
        comeco = data_prevista - timedelta(weeks=SEMANAS_DE_GESTACAO)
        return (
            comeco + timedelta(weeks=fase.inicio),
            comeco + timedelta(weeks=fase.fim + 1) - timedelta(days=1),
        )
    return (
        adicionar_meses(data_prevista, fase.inicio),
        adicionar_meses(data_prevista, fase.fim + 1) - timedelta(days=1),
    )


def montar_roteiro(
    fases: Iterable[Fase], data_prevista: date, hoje: date
) -> tuple[FaseCalculada, ...]:
    """Fases com datas reais, com uma marcada como atual.

    Fases podem se sobrepor (a reta final vai até a 42ª semana e invade os primeiros meses do
    bebê). Antes da data prevista vale a primeira fase que contém `hoje`, porque a gestação
    pode passar da data; a partir dela vale a mais avançada, já que arrumar a mala deixou de
    ser o próximo passo.
    """
    calculadas = []
    for fase in sorted(fases, key=lambda f: f.ordem):
        inicio, fim = intervalo_da_fase(fase, data_prevista)
        calculadas.append((fase, inicio, fim, inicio <= hoje <= fim))
    candidatas = [i for i, c in enumerate(calculadas) if c[3]]
    primeira_atual = None
    if candidatas:
        primeira_atual = candidatas[-1] if hoje >= data_prevista else candidatas[0]
    return tuple(
        FaseCalculada(f.codigo, f.nome, f.texto, inicio, fim, atual=(i == primeira_atual))
        for i, (f, inicio, fim, _) in enumerate(calculadas)
    )


def alertas_por_idade(
    regras: Iterable[RegraSegurancaCatalogo], data_prevista: date
) -> tuple[Alerta, ...]:
    """Regras de segurança com a data em que passam a valer, da mais cedo para a mais tarde."""
    alertas = [
        Alerta(
            codigo=r.codigo,
            tema=r.tema,
            texto=r.texto,
            base=r.base,
            ativo_a_partir=adicionar_meses(data_prevista, r.idade_inicio_meses),
            ativo_ate=adicionar_meses(data_prevista, r.idade_fim_meses),
            itens=r.itens,
        )
        for r in regras
    ]
    return tuple(sorted(alertas, key=lambda a: (a.ativo_a_partir, a.codigo)))
