import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { usePlanilha } from '../hooks/usePlanilha'
import { useMarcacao } from '../hooks/useMarcacao'
import type { LinhaSaida, MomentoCompra } from '../api/enxovais'
import { CabecalhoEnxoval } from './planilha/CabecalhoEnxoval'
import { EstadoPagina } from './planilha/EstadoPagina'
import { ResumoPlanilha } from './planilha/ResumoPlanilha'
import { FiltrosPlanilha, type Filtro } from './planilha/FiltrosPlanilha'
import { GrupoPlanilha } from './planilha/GrupoPlanilha'
import { PainelFases } from './planilha/PainelFases'

// Ordem de exibição dos grupos — atrasado sempre primeiro
const ORDEM_MOMENTOS: MomentoCompra[] = ['atrasado', 'agora', 'proxima_fase', 'futuro']

function filtrarLinhas(linhas: LinhaSaida[], filtro: Filtro, faseFiltrada: string | null): LinhaSaida[] {
  let resultado = linhas

  // Filtro de fase (painel de fases)
  if (faseFiltrada !== null) {
    resultado = resultado.filter((l) => l.fase_codigo === faseFiltrada)
  }

  // Filtro de prioridade/faltando
  switch (filtro) {
    case 'faltando':
      resultado = resultado.filter((l) => l.faltam > 0)
      break
    case 'essencial':
    case 'util':
    case 'pode_esperar':
      resultado = resultado.filter((l) => l.prioridade === filtro)
      break
  }

  return resultado
}

export default function Planilha() {
  const { id = '' } = useParams<{ id: string }>()
  const { data: enxoval, isLoading, isError, error } = usePlanilha(id)
  const { marcar, completar } = useMarcacao(id)
  const [filtro, setFiltro] = useState<Filtro>('todos')
  const [faseFiltrada, setFaseFiltrada] = useState<string | null>(null)

  if (isLoading || isError || !enxoval) {
    return <EstadoPagina isLoading={isLoading} isError={isError} error={error} />
  }

  const linhasFiltradas = filtrarLinhas(enxoval.linhas, filtro, faseFiltrada)
  const destacarJaTinha = enxoval.resumo.destacar_ja_tinha

  // Categorias ordenadas (fonte de verdade para nome e ordem)
  const categoriasOrdenadas = enxoval.categorias.slice().sort((a, b) => a.ordem - b.ordem)

  // Agrupamento primário por momento_compra, secundário por categoria
  const grupos = ORDEM_MOMENTOS.map((momento) => {
    const linhasDoMomento = linhasFiltradas.filter((l) => l.momento_compra === momento)
    const categorias = categoriasOrdenadas
      .map((cat) => ({
        ...cat,
        linhas: linhasDoMomento.filter((l) => l.categoria_slug === cat.slug),
      }))
      .filter((cat) => cat.linhas.length > 0)
    return { momento, categorias }
  }).filter((g) => g.categorias.length > 0)

  const semResultados = grupos.length === 0

  return (
    <div className="min-h-screen bg-fundo">
      <CabecalhoEnxoval enxoval={enxoval} abaAtiva="planilha" />

      <main className="mx-auto max-w-2xl space-y-4 p-4">
        <ResumoPlanilha enxoval={enxoval} />

        {enxoval.roteiro.length > 0 && (
          <PainelFases
            fases={enxoval.roteiro}
            linhas={enxoval.linhas}
            faseFiltrada={faseFiltrada}
            onFaseFiltrada={setFaseFiltrada}
          />
        )}

        <FiltrosPlanilha filtroAtivo={filtro} onChange={setFiltro} />

        {semResultados && (
          <p className="py-8 text-center text-texto-suave">
            Nenhum item corresponde ao filtro selecionado.
          </p>
        )}

        {grupos.map(({ momento, categorias }) => (
          <GrupoPlanilha
            key={momento}
            momento={momento}
            categorias={categorias}
            destacarJaTinha={destacarJaTinha}
            onMarcar={marcar}
            onCompletar={completar}
          />
        ))}
      </main>
    </div>
  )
}
