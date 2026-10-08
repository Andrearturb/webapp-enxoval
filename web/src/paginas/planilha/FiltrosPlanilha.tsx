export type Filtro =
  | 'todos'
  | 'faltando'
  | 'essencial'
  | 'util'
  | 'pode_esperar'

interface Props {
  filtroAtivo: Filtro
  onChange: (filtro: Filtro) => void
}

const FILTROS: { valor: Filtro; rotulo: string }[] = [
  { valor: 'todos', rotulo: 'Todos' },
  { valor: 'faltando', rotulo: 'Faltando' },
  { valor: 'essencial', rotulo: 'Essencial' },
  { valor: 'util', rotulo: 'Útil' },
  { valor: 'pode_esperar', rotulo: 'Pode esperar' },
]

export function FiltrosPlanilha({ filtroAtivo, onChange }: Props) {
  return (
    <div
      className="flex flex-wrap gap-2"
      role="group"
      aria-label="Filtros da planilha"
    >
      {FILTROS.map(({ valor, rotulo }) => (
        <button
          key={valor}
          type="button"
          onClick={() => onChange(valor)}
          className={`min-h-11 rounded-full border px-3.5 py-2 text-xs font-medium transition-colors sm:text-sm ${
            filtroAtivo === valor
              ? 'border-principal bg-principal text-white'
              : 'border-borda bg-superficie text-texto-suave hover:border-principal hover:text-principal'
          }`}
          aria-pressed={filtroAtivo === valor}
        >
          {rotulo}
        </button>
      ))}
    </div>
  )
}
