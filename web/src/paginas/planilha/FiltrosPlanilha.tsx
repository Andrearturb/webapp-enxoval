export type Filtro = 'todos' | 'faltando' | 'essencial' | 'util' | 'pode_esperar'

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
    <div className="flex flex-wrap gap-2" role="group" aria-label="Filtros da planilha">
      {FILTROS.map(({ valor, rotulo }) => (
        <button
          key={valor}
          type="button"
          onClick={() => onChange(valor)}
          className={`rounded-xl px-3 py-1.5 text-sm font-medium transition-colors ${
            filtroAtivo === valor
              ? 'bg-principal text-white'
              : 'bg-principal-suave text-texto-suave hover:bg-principal hover:text-white'
          }`}
          aria-pressed={filtroAtivo === valor}
        >
          {rotulo}
        </button>
      ))}
    </div>
  )
}
