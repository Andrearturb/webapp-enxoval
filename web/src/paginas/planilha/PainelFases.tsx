import type { FaseSaida, LinhaSaida } from '../../api/enxovais'

interface Props {
  fases: FaseSaida[]
  linhas: LinhaSaida[]
  faseFiltrada: string | null
  onFaseFiltrada: (codigo: string | null) => void
}

export function PainelFases({
  fases,
  linhas,
  faseFiltrada,
  onFaseFiltrada,
}: Props) {
  // Contagem de itens por fase
  const contagemPorFase = new Map<string, number>()
  for (const linha of linhas) {
    contagemPorFase.set(
      linha.fase_codigo,
      (contagemPorFase.get(linha.fase_codigo) ?? 0) + 1,
    )
  }

  // Determina a ordem da fase atual para saber quais são "passadas"
  const ordemAtual = fases.findIndex((f) => f.atual)

  // Mantém a ordem do roteiro, exibe só fases com itens (exceto fases passadas com itens não comprados — essas sempre aparecem)
  const cardsVisiveis = fases.filter((fase) => {
    const count = contagemPorFase.get(fase.codigo) ?? 0
    const indiceFase = fases.findIndex((f) => f.codigo === fase.codigo)
    const ePassada = ordemAtual >= 0 && indiceFase < ordemAtual

    if (ePassada) {
      // Fase passada: mostrar se tem itens com faltam > 0
      const temPendentes = linhas.some(
        (l) => l.fase_codigo === fase.codigo && l.faltam > 0,
      )
      return temPendentes
    }

    return count > 0
  })

  if (cardsVisiveis.length === 0) return null

  return (
    <div
      className="flex gap-2 overflow-x-auto pb-1"
      role="group"
      aria-label="Filtro por fase"
    >
      {cardsVisiveis.map((fase) => {
        const count = contagemPorFase.get(fase.codigo) ?? 0
        const indiceFase = fases.findIndex((f) => f.codigo === fase.codigo)
        const ePassada = ordemAtual >= 0 && indiceFase < ordemAtual
        const temPendentes =
          ePassada &&
          linhas.some((l) => l.fase_codigo === fase.codigo && l.faltam > 0)
        const eSelecionada = faseFiltrada === fase.codigo
        const eAtual = fase.atual

        const classeBase =
          'relative flex min-h-16 shrink-0 flex-col items-start rounded-2xl border border-borda px-4 py-3 text-sm transition-colors'
        const classeEstado =
          eSelecionada || eAtual
            ? 'bg-principal text-white font-semibold'
            : 'bg-superficie text-texto hover:bg-principal-suave'

        return (
          <button
            key={fase.codigo}
            type="button"
            className={`${classeBase} ${classeEstado}`}
            onClick={() => onFaseFiltrada(eSelecionada ? null : fase.codigo)}
            aria-pressed={eSelecionada}
          >
            <span className="font-medium leading-snug">{fase.nome}</span>
            <span className="mt-0.5 text-xs">
              {count} {count === 1 ? 'item' : 'itens'}
            </span>
            {temPendentes && (
              <span
                data-testid="badge-alerta"
                className="absolute right-1.5 top-1.5 size-2 rounded-full bg-alerta-texto"
                aria-label="itens pendentes"
              />
            )}
          </button>
        )
      })}
    </div>
  )
}
