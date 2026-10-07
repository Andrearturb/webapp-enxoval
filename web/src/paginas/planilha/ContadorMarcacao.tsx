import type { LinhaSaida } from '../../api/enxovais'

type Origem = 'comprada' | 'ganhada' | 'ja_tinha'

interface Props {
  linha: LinhaSaida
  destacarJaTinha: boolean
  onMarcar: (marcacao: { comprada: number; ganhada: number; ja_tinha: number }) => void
  onCompletar: (origem: Origem) => void
}

const ORIGENS: { valor: Origem; rotulo: string }[] = [
  { valor: 'comprada', rotulo: 'Comprada' },
  { valor: 'ganhada', rotulo: 'Ganhada' },
  { valor: 'ja_tinha', rotulo: 'Já tinha' },
]

export function ContadorMarcacao({ linha, destacarJaTinha, onMarcar, onCompletar }: Props) {
  const origens = destacarJaTinha
    ? [ORIGENS[2], ORIGENS[0], ORIGENS[1]]
    : ORIGENS

  function incrementar(origem: Origem) {
    onMarcar({
      comprada: linha.comprada + (origem === 'comprada' ? 1 : 0),
      ganhada: linha.ganhada + (origem === 'ganhada' ? 1 : 0),
      ja_tinha: linha.ja_tinha + (origem === 'ja_tinha' ? 1 : 0),
    })
  }

  function decrementar(origem: Origem) {
    const atual = linha[origem]
    if (atual <= 0) return
    onMarcar({
      comprada: linha.comprada - (origem === 'comprada' ? 1 : 0),
      ganhada: linha.ganhada - (origem === 'ganhada' ? 1 : 0),
      ja_tinha: linha.ja_tinha - (origem === 'ja_tinha' ? 1 : 0),
    })
  }

  return (
    <div className="mt-2 flex flex-col gap-2">
      {origens.map(({ valor, rotulo }) => (
        <div key={valor} className="flex items-center gap-2">
          <span className="w-20 text-xs text-texto-suave">{rotulo}</span>
          <div className="flex items-center gap-1">
            <button
              type="button"
              aria-label={`- ${rotulo}`}
              onClick={() => decrementar(valor)}
              disabled={linha[valor] <= 0}
              className="flex h-8 w-8 items-center justify-center rounded-lg bg-principal-suave text-principal disabled:opacity-30"
            >
              −
            </button>
            <span className="w-6 text-center tabular-nums">{linha[valor]}</span>
            <button
              type="button"
              aria-label={`+ ${rotulo}`}
              onClick={() => incrementar(valor)}
              className="flex h-8 w-8 items-center justify-center rounded-lg bg-principal-suave text-principal"
            >
              +
            </button>
          </div>
        </div>
      ))}
      {linha.faltam > 0 && (
        <button
          type="button"
          onClick={() => onCompletar('comprada')}
          className="mt-1 self-start rounded-xl bg-principal px-3 py-1.5 text-xs text-white"
        >
          Marcar tudo como comprada
        </button>
      )}
    </div>
  )
}
