import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { usePlanilha } from '../hooks/usePlanilha'
import { apagarEnxoval } from '../api/enxovais'
import { ErroApi } from '../api/cliente'
import { CabecalhoEnxoval } from './planilha/CabecalhoEnxoval'
import { EstadoPagina } from './planilha/EstadoPagina'
import { Button } from '../componentes/ui/button'

const ROTULOS_MORADIA: Record<string, string> = {
  apartamento: 'Apartamento',
  casa_sem_escada: 'Casa sem escada',
  casa_com_escada: 'Casa com escada',
}

const ROTULOS_ORCAMENTO: Record<string, string> = {
  economico: 'Econômico',
  intermediario: 'Intermediário',
  investir: 'Investir mais',
}

const ROTULOS_LAVAGEM: Record<number, string> = {
  1: 'Todo dia',
  2: 'A cada 2 dias',
  3: 'A cada 3 dias',
  4: '2× por semana',
}

function RespostaItem({ rotulo, valor }: { rotulo: string; valor: string }) {
  return (
    <div className="flex justify-between gap-4 py-2 text-sm">
      <span className="text-texto-suave">{rotulo}</span>
      <span className="font-medium text-texto">{valor}</span>
    </div>
  )
}

export default function Ajustes() {
  const { id = '' } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { data: enxoval, isLoading, isError, error } = usePlanilha(id)

  const [confirmandoApagar, setConfirmandoApagar] = useState(false)
  const [linkCopiado, setLinkCopiado] = useState(false)
  const [erroApagar, setErroApagar] = useState<string | null>(null)

  const mutacaoApagar = useMutation({
    mutationFn: () => apagarEnxoval(id),
    onSuccess: () => {
      qc.removeQueries({ queryKey: ['enxoval', id] })
      navigate('/questionario/1', { replace: true })
    },
    onError: (e) => {
      setErroApagar(e instanceof ErroApi ? e.message : 'Não foi possível apagar. Tente de novo.')
      setConfirmandoApagar(false)
    },
  })

  async function copiarLink() {
    const url = `${window.location.origin}/enxoval/${id}/planilha`
    try {
      await navigator.clipboard.writeText(url)
      setLinkCopiado(true)
      setTimeout(() => setLinkCopiado(false), 2500)
    } catch {
      // fallback silencioso — clipboard pode ser bloqueado em alguns browsers
    }
  }

  if (isLoading || isError || !enxoval) {
    return <EstadoPagina isLoading={isLoading} isError={isError} error={error} />
  }

  const r = enxoval.respostas
  const dataFormatada = new Date(r.data_prevista + 'T12:00:00').toLocaleDateString('pt-BR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })

  return (
    <div className="min-h-screen bg-fundo">
      <CabecalhoEnxoval enxoval={enxoval} abaAtiva="ajustes" />

      <main className="mx-auto max-w-2xl space-y-5 px-4 py-6">
        <h1 className="font-titulo text-xl font-semibold text-texto">Ajustes</h1>

        {/* Resumo das respostas */}
        <section className="rounded-2xl bg-superficie p-4 shadow-sm">
          <h2 className="mb-3 font-semibold text-texto">Respostas do questionário</h2>
          <div className="divide-y divide-principal-suave">
            <RespostaItem rotulo="Cidade" valor={`${r.municipio.nome} - ${r.municipio.uf}`} />
            <RespostaItem rotulo="Data prevista" valor={dataFormatada} />
            <RespostaItem
              rotulo="Frequência de lavagem"
              valor={ROTULOS_LAVAGEM[r.dias_entre_lavagens] ?? `A cada ${r.dias_entre_lavagens} dias`}
            />
            <RespostaItem rotulo="Moradia" valor={ROTULOS_MORADIA[r.moradia] ?? r.moradia} />
            <RespostaItem rotulo="Tem carro" valor={r.tem_carro ? 'Sim' : 'Não'} />
            <RespostaItem rotulo="Orçamento" valor={ROTULOS_ORCAMENTO[r.orcamento] ?? r.orcamento} />
            <RespostaItem rotulo="Primeiro filho" valor={r.primeiro_filho ? 'Sim' : 'Não'} />
          </div>
          <p className="mt-3 text-xs text-texto-suave">
            Para corrigir as respostas, crie um novo enxoval a partir da{' '}
            <a href="/questionario/1" className="underline hover:text-principal">
              página inicial
            </a>
            .
          </p>
        </section>

        {/* Exportar */}
        <section className="rounded-2xl bg-superficie p-4 shadow-sm">
          <h2 className="mb-1 font-semibold text-texto">Exportar</h2>
          <p className="mb-3 text-sm text-texto-suave">
            Baixe sua lista personalizada em diferentes formatos.
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              href={`/api/v1/enxovais/${id}/exportar.xlsx`}
              download
              className="inline-flex items-center gap-1.5 rounded-xl bg-principal-suave px-3 py-2 text-sm font-medium text-texto-suave transition-colors hover:bg-principal hover:text-white"
            >
              📊 Baixar XLSX
            </a>
            <a
              href={`/api/v1/enxovais/${id}/exportar.csv`}
              download
              className="inline-flex items-center gap-1.5 rounded-xl bg-principal-suave px-3 py-2 text-sm font-medium text-texto-suave transition-colors hover:bg-principal hover:text-white"
            >
              📄 Baixar CSV
            </a>
            <a
              href={`/api/v1/enxovais/${id}/exportar.pdf`}
              download
              className="inline-flex items-center gap-1.5 rounded-xl bg-principal-suave px-3 py-2 text-sm font-medium text-texto-suave transition-colors hover:bg-principal hover:text-white"
            >
              📑 Baixar PDF
            </a>
          </div>
        </section>

        {/* Copiar link */}
        <section className="rounded-2xl bg-superficie p-4 shadow-sm">
          <h2 className="mb-1 font-semibold text-texto">Compartilhar</h2>
          <p className="mb-3 text-sm text-texto-suave">
            Copie o link para acessar esta planilha em outro aparelho ou compartilhar com alguém.
          </p>
          <Button type="button" onClick={copiarLink} variant="secundario">
            {linkCopiado ? '✓ Link copiado!' : 'Copiar link'}
          </Button>
        </section>

        {/* Apagar dados */}
        <section className="rounded-2xl bg-superficie p-4 shadow-sm">
          <h2 className="mb-1 font-semibold text-texto">Apagar meus dados</h2>
          <p className="mb-3 text-sm text-texto-suave">
            Remove permanentemente este enxoval e todas as quantidades marcadas. Não é possível desfazer.
          </p>

          {erroApagar && (
            <p role="alert" className="mb-3 rounded-xl bg-alerta-fundo p-3 text-sm text-alerta-texto">
              {erroApagar}
            </p>
          )}

          {!confirmandoApagar ? (
            <Button
              type="button"
              variant="secundario"
              onClick={() => {
                setErroApagar(null)
                setConfirmandoApagar(true)
              }}
            >
              Apagar meus dados
            </Button>
          ) : (
            <div className="flex flex-wrap gap-3">
              <Button
                type="button"
                onClick={() => mutacaoApagar.mutate()}
                disabled={mutacaoApagar.isPending}
              >
                {mutacaoApagar.isPending ? 'Apagando...' : 'Confirmar exclusão'}
              </Button>
              <Button
                type="button"
                variant="secundario"
                onClick={() => setConfirmandoApagar(false)}
                disabled={mutacaoApagar.isPending}
              >
                Cancelar
              </Button>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
