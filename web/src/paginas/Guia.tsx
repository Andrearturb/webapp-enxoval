import { Link, useParams } from 'react-router-dom'
import { usePlanilha } from '../hooks/usePlanilha'
import { CabecalhoEnxoval } from './planilha/CabecalhoEnxoval'
import { EstadoPagina } from './planilha/EstadoPagina'
import type { components } from '../api/tipos'

type FichaSaida = components['schemas']['FichaSaida']

function idadeTexto(meses: number): string {
  if (meses === 0) return 'Do nascimento'
  if (meses === 1) return 'A partir de 1 mês'
  return `A partir de ${meses} meses`
}

function CartaoFicha({ ficha, id }: { ficha: FichaSaida; id: string }) {
  const temSeguranca = ficha.regras_seguranca.length > 0

  return (
    <Link
      to={`/enxoval/${id}/guia/${ficha.slug}`}
      className="block rounded-2xl bg-superficie p-4 shadow-sm hover:shadow-md transition-shadow"
    >
      <div className="flex items-start justify-between gap-2">
        <h2 className="font-titulo font-semibold text-texto">{ficha.nome}</h2>
        {temSeguranca && (
          <span className="shrink-0 rounded bg-alerta-fundo px-1.5 py-0.5 text-xs text-alerta-texto">
            Segurança
          </span>
        )}
      </div>
      <p className="mt-1 text-sm text-texto-suave line-clamp-2">{ficha.para_que_serve}</p>
      <p className="mt-2 text-xs text-texto-suave">{idadeTexto(ficha.idade_inicio_meses)}</p>
    </Link>
  )
}

export default function Guia() {
  const { id = '' } = useParams<{ id: string }>()
  const { data: enxoval, isLoading, isError, error } = usePlanilha(id)

  if (isLoading || isError || !enxoval) {
    return <EstadoPagina isLoading={isLoading} isError={isError} error={error} />
  }

  return (
    <div className="min-h-screen bg-fundo">
      <CabecalhoEnxoval enxoval={enxoval} abaAtiva="guia" />

      <main className="mx-auto max-w-2xl px-4 py-6">
        <h1 className="mb-6 font-titulo text-xl font-semibold text-texto">Guia dos itens</h1>

        {enxoval.fichas.length === 0 ? (
          <p className="text-texto-suave">Nenhuma ficha disponível.</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {enxoval.fichas.map((ficha) => (
              <CartaoFicha key={ficha.slug} ficha={ficha} id={id} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
