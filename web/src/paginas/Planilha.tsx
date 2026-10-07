import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { usePlanilha } from '../hooks/usePlanilha'
import { useMarcacao } from '../hooks/useMarcacao'
import { ErroApi } from '../api/cliente'
import type { LinhaSaida } from '../api/enxovais'
import { CabecalhoPlanilha } from './planilha/CabecalhoPlanilha'
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

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-fundo">
        <p className="text-texto-suave">Carregando planilha...</p>
      </div>
    )
  }

  if (isError) {
    const status = error instanceof ErroApi ? error.status : 0
    const mensagem =
      status === 404
        ? 'Enxoval não encontrado. Verifique o link ou crie um novo enxoval.'
        : error instanceof Error
          ? error.message
          : 'Não foi possível carregar o enxoval.'

    return (
      <div className="flex min-h-screen items-center justify-center bg-fundo p-4">
        <div className="rounded-2xl bg-superficie p-6 shadow-sm text-center max-w-sm">
          <p className="text-texto">{mensagem}</p>
        </div>
      </div>
    )
  }

  if (!enxoval) return null

  const linhasFiltradas = filtrarLinhas(enxoval.linhas, filtro)
  const destacarJaTinha = enxoval.resumo.destacar_ja_tinha

  // Agrupa linhas filtradas por categoria, mantendo a ordem do catálogo
  const categoriasPorSlug = Object.fromEntries(enxoval.categorias.map((c) => [c.slug, c]))
  const categorias = enxoval.categorias
    .slice()
    .sort((a, b) => a.ordem - b.ordem)
    .map((cat) => ({
      ...cat,
      linhas: linhasFiltradas.filter((l) => l.categoria_slug === cat.slug),
    }))
    .filter((cat) => cat.linhas.length > 0)

  // Suprime aviso de variável não usada (categoriasPorSlug é construído mas não usado aqui)
  void categoriasPorSlug

  return (
    <div className="min-h-screen bg-fundo">
      <CabecalhoPlanilha enxoval={enxoval} />

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
