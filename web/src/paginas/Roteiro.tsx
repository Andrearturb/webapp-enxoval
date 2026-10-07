import { useParams } from 'react-router-dom'
import { usePlanilha } from '../hooks/usePlanilha'
import { CabecalhoEnxoval } from './planilha/CabecalhoEnxoval'
import { EstadoPagina } from './planilha/EstadoPagina'
import type { components } from '../api/tipos'

type FaseSaida = components['schemas']['FaseSaida']

function formatarIntervalo(inicio: string, fim: string): string {
  const opcoes: Intl.DateTimeFormatOptions = { month: 'short', year: 'numeric' }
  const i = new Date(inicio + 'T12:00:00').toLocaleDateString('pt-BR', opcoes)
  const f = new Date(fim + 'T12:00:00').toLocaleDateString('pt-BR', opcoes)
  return `${i} – ${f}`
}

function CardFase({ fase }: { fase: FaseSaida }) {
  return (
    <li
      data-testid="fase"
      data-atual={fase.atual ? 'true' : 'false'}
      className={`relative rounded-2xl p-4 shadow-sm ${
        fase.atual ? 'bg-principal text-white' : 'bg-superficie text-texto'
      }`}
    >
      {/* Marcador da linha do tempo */}
      <div
        className={`absolute -left-3 top-5 h-4 w-4 rounded-full border-2 ${
          fase.atual
            ? 'border-principal bg-white'
            : 'border-principal-suave bg-white'
        }`}
        aria-hidden
      />

      <div className="flex flex-wrap items-start justify-between gap-2">
        <h2 className={`font-titulo font-semibold ${fase.atual ? 'text-white' : 'text-texto'}`}>
          {fase.nome}
        </h2>
        {fase.atual && (
          <span className="rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-principal">
            Fase atual
          </span>
        )}
      </div>

      <p className={`mt-0.5 text-sm ${fase.atual ? 'text-white' : 'text-texto-suave'}`}>
        {formatarIntervalo(fase.inicio, fase.fim)}
      </p>

      <p className={`mt-2 text-sm leading-relaxed ${fase.atual ? 'text-white' : 'text-texto'}`}>
        {fase.texto}
      </p>
    </li>
  )
}

export default function Roteiro() {
  const { id = '' } = useParams<{ id: string }>()
  const { data: enxoval, isLoading, isError, error } = usePlanilha(id)

  if (isLoading || isError || !enxoval) {
    return <EstadoPagina isLoading={isLoading} isError={isError} error={error} />
  }

  return (
    <div className="min-h-screen bg-fundo">
      <CabecalhoEnxoval enxoval={enxoval} abaAtiva="roteiro" />

      <main className="mx-auto max-w-2xl px-4 py-6">
        <h1 className="mb-6 font-titulo text-xl font-semibold text-texto">Roteiro de compras</h1>

        {enxoval.roteiro.length === 0 ? (
          <p className="text-texto-suave">Nenhuma fase disponível.</p>
        ) : (
          <ol className="relative ml-3 space-y-4 border-l-2 border-principal-suave pl-6">
            {enxoval.roteiro.map((fase) => (
              <CardFase key={fase.codigo} fase={fase} />
            ))}
          </ol>
        )}
      </main>
    </div>
  )
}
