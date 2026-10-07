import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { usePlanilha } from '../hooks/usePlanilha'
import { CabecalhoEnxoval } from './planilha/CabecalhoEnxoval'
import { EstadoPagina } from './planilha/EstadoPagina'
import type { components } from '../api/tipos'

type AlertaSaida = components['schemas']['AlertaSaida']
type TemaSeguranca = components['schemas']['TemaSeguranca']

const TEMAS: { valor: TemaSeguranca | 'todos'; rotulo: string }[] = [
  { valor: 'todos', rotulo: 'Todos' },
  { valor: 'sono', rotulo: 'Sono' },
  { valor: 'transporte', rotulo: 'Transporte' },
  { valor: 'banho', rotulo: 'Banho' },
  { valor: 'alimentacao', rotulo: 'Alimentação' },
  { valor: 'casa', rotulo: 'Casa' },
  { valor: 'brinquedos', rotulo: 'Brinquedos' },
  { valor: 'geral', rotulo: 'Geral' },
]

function formatarData(dataStr: string): string {
  return new Date(dataStr + 'T12:00:00').toLocaleDateString('pt-BR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

function CardAlerta({ alerta }: { alerta: AlertaSaida }) {
  return (
    <li className="rounded-2xl bg-alerta-fundo p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <p className="flex-1 text-sm font-medium leading-relaxed text-alerta-texto">
          {alerta.texto}
        </p>
        <span className="shrink-0 rounded bg-white/50 px-2 py-0.5 text-xs font-medium text-alerta-texto">
          {alerta.base}
        </span>
      </div>
      <p className="mt-2 text-xs text-alerta-texto/70">
        Ativo de {formatarData(alerta.ativo_a_partir)} a {formatarData(alerta.ativo_ate)}
      </p>
    </li>
  )
}

export default function Seguranca() {
  const { id = '' } = useParams<{ id: string }>()
  const { data: enxoval, isLoading, isError, error } = usePlanilha(id)
  const [temaAtivo, setTemaAtivo] = useState<TemaSeguranca | 'todos'>('todos')

  if (isLoading || isError || !enxoval) {
    return <EstadoPagina isLoading={isLoading} isError={isError} error={error} />
  }

  // Filtra apenas temas que têm alertas no enxoval
  const temasComAlertas = new Set(enxoval.alertas.map((a) => a.tema))
  const filtrosVisiveis = TEMAS.filter(
    (t) => t.valor === 'todos' || temasComAlertas.has(t.valor),
  )

  const alertasFiltrados =
    temaAtivo === 'todos'
      ? enxoval.alertas
      : enxoval.alertas.filter((a) => a.tema === temaAtivo)

  return (
    <div className="min-h-screen bg-fundo">
      <CabecalhoEnxoval enxoval={enxoval} abaAtiva="seguranca" />

      <main className="mx-auto max-w-2xl px-4 py-6">
        <h1 className="mb-2 font-titulo text-xl font-semibold text-texto">Segurança</h1>
        <p className="mb-5 text-sm text-texto-suave">
          Regras baseadas em recomendações da SBP, INMETRO e CONTRAN. Confirme com seu pediatra.
        </p>

        {/* Filtros de tema */}
        {filtrosVisiveis.length > 1 && (
          <div className="mb-5 flex flex-wrap gap-2" role="group" aria-label="Filtrar por tema">
            {filtrosVisiveis.map(({ valor, rotulo }) => (
              <button
                key={valor}
                type="button"
                onClick={() => setTemaAtivo(valor)}
                aria-pressed={temaAtivo === valor}
                className={`rounded-xl px-3 py-1.5 text-sm font-medium transition-colors ${
                  temaAtivo === valor
                    ? 'bg-principal text-white'
                    : 'bg-principal-suave text-texto-suave hover:bg-principal hover:text-white'
                }`}
              >
                {rotulo}
              </button>
            ))}
          </div>
        )}

        {alertasFiltrados.length === 0 ? (
          <p className="py-8 text-center text-texto-suave">
            Nenhum alerta para o filtro selecionado.
          </p>
        ) : (
          <ul className="space-y-3">
            {alertasFiltrados.map((alerta) => (
              <CardAlerta key={alerta.codigo} alerta={alerta} />
            ))}
          </ul>
        )}
      </main>
    </div>
  )
}
