import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { usePlanilha } from '../hooks/usePlanilha'
import { apagarEnxoval } from '../api/enxovais'
import { apiDownload, ErroApi } from '../api/cliente'
import { keycloakHabilitado } from '../auth/keycloak'
import { useAuth } from '../auth/AuthProvider'
import { CabecalhoEnxoval } from './planilha/CabecalhoEnxoval'
import { EstadoPagina } from './planilha/EstadoPagina'
import { Button } from '../componentes/ui/button'
import { Download, FileSpreadsheet, FileText } from 'lucide-react'
import { EditarRespostas } from './ajustes/EditarRespostas'

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
  const { sair, nomeUsuario } = useAuth()

  const [confirmandoApagar, setConfirmandoApagar] = useState(false)
  const [erroApagar, setErroApagar] = useState<string | null>(null)
  const [erroExportar, setErroExportar] = useState<string | null>(null)
  const [editando, setEditando] = useState(false)
  const [salvou, setSalvou] = useState(false)

  async function exportar(
    evento: React.MouseEvent<HTMLAnchorElement>,
    formato: string,
  ) {
    if (!keycloakHabilitado) return
    evento.preventDefault()
    setErroExportar(null)
    try {
      await apiDownload(
        `/enxovais/${id}/exportar.${formato}`,
        `enxoval-${id}.${formato}`,
      )
    } catch (erro) {
      setErroExportar(
        erro instanceof ErroApi
          ? erro.message
          : 'Não foi possível exportar. Tente de novo.',
      )
    }
  }

  const mutacaoApagar = useMutation({
    mutationFn: () => apagarEnxoval(id),
    onSuccess: () => {
      qc.removeQueries({ queryKey: ['enxoval', id] })
      void qc.invalidateQueries({ queryKey: ['meus-enxovais'] })
      navigate('/meus-enxovais', { replace: true })
    },
    onError: (e) => {
      setErroApagar(
        e instanceof ErroApi
          ? e.message
          : 'Não foi possível apagar. Tente de novo.',
      )
      setConfirmandoApagar(false)
    },
  })

  if (isLoading || isError || !enxoval) {
    return (
      <EstadoPagina isLoading={isLoading} isError={isError} error={error} />
    )
  }

  const r = enxoval.respostas
  const dataFormatada = new Date(
    r.data_prevista + 'T12:00:00',
  ).toLocaleDateString('pt-BR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })

  return (
    <div className="min-h-screen bg-fundo">
      <CabecalhoEnxoval enxoval={enxoval} abaAtiva="ajustes" />

      <main className="mx-auto max-w-3xl space-y-5 px-4 py-6 sm:px-6 sm:py-8">
        <h1 className="font-titulo text-3xl font-semibold text-texto">
          Ajustes
        </h1>

        {/* Resumo das respostas */}
        <section className="rounded-3xl border border-borda bg-superficie p-5 sm:p-6">
          <h2 className="mb-3 font-semibold text-texto">
            Respostas do questionário
          </h2>
          {salvou && (
            <p
              role="status"
              className="mb-4 rounded-xl bg-principal-suave p-3 text-sm text-principal"
            >
              Enxoval atualizado. Suas compras, presentes e itens que já tinha
              foram preservados.
            </p>
          )}
          {!editando && (
            <div className="divide-y divide-principal-suave">
              <RespostaItem
                rotulo="Cidade"
                valor={`${r.municipio.nome} - ${r.municipio.uf}`}
              />
              <RespostaItem rotulo="Data prevista" valor={dataFormatada} />
              <RespostaItem
                rotulo="Frequência de lavagem"
                valor={
                  ROTULOS_LAVAGEM[r.dias_entre_lavagens] ??
                  `A cada ${r.dias_entre_lavagens} dias`
                }
              />
              <RespostaItem
                rotulo="Moradia"
                valor={ROTULOS_MORADIA[r.moradia] ?? r.moradia}
              />
              <RespostaItem
                rotulo="Tem carro"
                valor={r.tem_carro ? 'Sim' : 'Não'}
              />
              <RespostaItem
                rotulo="Orçamento"
                valor={ROTULOS_ORCAMENTO[r.orcamento] ?? r.orcamento}
              />
              <RespostaItem
                rotulo="Primeiro filho"
                valor={r.primeiro_filho ? 'Sim' : 'Não'}
              />
            </div>
          )}
          {editando ? (
            <EditarRespostas
              key={id}
              enxoval={enxoval}
              onFechar={(atualizou) => {
                setEditando(false)
                setSalvou(atualizou)
              }}
            />
          ) : (
            <div className="mt-4 space-y-3">
              <p className="text-sm text-texto-suave">
                Você pode mudar suas respostas e adaptar este enxoval sem perder
                os itens já registrados.
              </p>
              <Button
                type="button"
                variant="secundario"
                onClick={() => {
                  setEditando(true)
                  setSalvou(false)
                }}
              >
                Editar respostas
              </Button>
            </div>
          )}
        </section>

        {/* Exportar */}
        <section className="rounded-3xl border border-borda bg-superficie p-5 sm:p-6">
          <h2 className="mb-1 font-semibold text-texto">Exportar</h2>
          <p className="mb-3 text-sm text-texto-suave">
            Baixe sua lista personalizada em diferentes formatos.
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              href={`/api/v1/enxovais/${id}/exportar.xlsx`}
              onClick={(evento) => void exportar(evento, 'xlsx')}
              download
              className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-principal-suave px-4 py-3 text-sm font-medium text-principal transition-colors hover:bg-principal hover:text-white"
            >
              <FileSpreadsheet size={17} aria-hidden="true" /> Baixar XLSX
            </a>
            <a
              href={`/api/v1/enxovais/${id}/exportar.csv`}
              onClick={(evento) => void exportar(evento, 'csv')}
              download
              className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-principal-suave px-4 py-3 text-sm font-medium text-principal transition-colors hover:bg-principal hover:text-white"
            >
              <FileText size={17} aria-hidden="true" /> Baixar CSV
            </a>
            <a
              href={`/api/v1/enxovais/${id}/exportar.pdf`}
              onClick={(evento) => void exportar(evento, 'pdf')}
              download
              className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-principal-suave px-4 py-3 text-sm font-medium text-principal transition-colors hover:bg-principal hover:text-white"
            >
              <Download size={17} aria-hidden="true" /> Baixar PDF
            </a>
          </div>
          {erroExportar && (
            <p role="alert" className="mt-3 text-alerta-texto">
              {erroExportar}
            </p>
          )}
        </section>

        {/* Conta */}
        {nomeUsuario && (
          <section className="rounded-3xl border border-borda bg-superficie p-5 sm:p-6">
            <h2 className="mb-1 font-semibold text-texto">Conta</h2>
            <p className="mb-3 text-sm text-texto-suave">
              Logado como{' '}
              <span className="font-medium text-texto">{nomeUsuario}</span>.
            </p>
            <Button type="button" variant="secundario" onClick={sair}>
              Sair
            </Button>
            <Link
              to="/minha-conta"
              className="ml-3 inline-flex min-h-11 items-center text-sm text-principal underline"
            >
              Minha conta
            </Link>
          </section>
        )}

        {/* Apagar dados */}
        <section className="rounded-3xl border border-borda bg-superficie p-5 sm:p-6">
          <h2 className="mb-1 font-semibold text-texto">Apagar meus dados</h2>
          <p className="mb-3 text-sm text-texto-suave">
            Remove permanentemente este enxoval e todas as quantidades marcadas.
            Não é possível desfazer.
          </p>

          {erroApagar && (
            <p
              role="alert"
              className="mb-3 rounded-xl bg-alerta-fundo p-3 text-sm text-alerta-texto"
            >
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
