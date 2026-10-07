import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { usePlanilha } from '../hooks/usePlanilha'
import { useMarcacao } from '../hooks/useMarcacao'
import type { LinhaSaida } from '../api/enxovais'
import { CabecalhoEnxoval } from './planilha/CabecalhoEnxoval'
import { EstadoPagina } from './planilha/EstadoPagina'
import { ResumoPlanilha } from './planilha/ResumoPlanilha'
import { FiltrosPlanilha, type Filtro } from './planilha/FiltrosPlanilha'
import { CategoriaPlanilha } from './planilha/CategoriaPlanilha'

function filtrarLinhas(linhas: LinhaSaida[], filtro: Filtro): LinhaSaida[] {
  switch (filtro) {
    case 'faltando':
      return linhas.filter((l) => l.faltam > 0)
    case 'essencial':
    case 'util':
    case 'pode_esperar':
      return linhas.filter((l) => l.prioridade === filtro)
    default:
      return linhas
  }
}

export default function Planilha() {
  const { id = '' } = useParams<{ id: string }>()
  const { data: enxoval, isLoading, isError, error } = usePlanilha(id)
  const { marcar, completar } = useMarcacao(id)
  const [filtro, setFiltro] = useState<Filtro>('todos')

  if (isLoading || isError || !enxoval) {
    return <EstadoPagina isLoading={isLoading} isError={isError} error={error} />
  }

  const linhasFiltradas = filtrarLinhas(enxoval.linhas, filtro)
  const destacarJaTinha = enxoval.resumo.destacar_ja_tinha

  // Agrupa linhas filtradas por categoria, mantendo a ordem do catálogo
  const categorias = enxoval.categorias
    .slice()
    .sort((a, b) => a.ordem - b.ordem)
    .map((cat) => ({
      ...cat,
      linhas: linhasFiltradas.filter((l) => l.categoria_slug === cat.slug),
    }))
    .filter((cat) => cat.linhas.length > 0)

  return (
    <div className="min-h-screen bg-fundo">
      <CabecalhoEnxoval enxoval={enxoval} abaAtiva="planilha" />

      <main className="mx-auto max-w-2xl space-y-4 p-4">
        <ResumoPlanilha enxoval={enxoval} />

        <FiltrosPlanilha filtroAtivo={filtro} onChange={setFiltro} />

        {categorias.length === 0 && (
          <p className="py-8 text-center text-texto-suave">
            Nenhum item corresponde ao filtro selecionado.
          </p>
        )}

        {categorias.map((cat) => (
          <CategoriaPlanilha
            key={cat.slug}
            nome={cat.nome}
            linhas={cat.linhas}
            destacarJaTinha={destacarJaTinha}
            onMarcar={marcar}
            onCompletar={completar}
          />
        ))}
      </main>
    </div>
  )
}
