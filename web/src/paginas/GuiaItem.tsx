import { Link, useParams } from 'react-router-dom'
import { usePlanilha } from '../hooks/usePlanilha'
import { EstadoPagina } from './planilha/EstadoPagina'
import { CabecalhoEnxoval } from './planilha/CabecalhoEnxoval'

const ROTULOS_FAIXA: Record<string, string> = {
  economico: 'Econômico',
  intermediario: 'Intermediário',
  investir: 'Investir',
}

export default function GuiaItem() {
  const { id = '', item: slug = '' } = useParams<{ id: string; item: string }>()
  const { data: enxoval, isLoading, isError, error } = usePlanilha(id)

  if (isLoading || isError || !enxoval) {
    return (
      <EstadoPagina isLoading={isLoading} isError={isError} error={error} />
    )
  }

  const ficha = enxoval.fichas.find((f) => f.slug === slug)

  if (!ficha) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-fundo p-4">
        <div className="max-w-sm rounded-2xl bg-superficie p-6 text-center shadow-sm">
          <p className="text-texto">Item não encontrado.</p>
          <Link
            to={`/enxoval/${id}/guia`}
            className="mt-4 inline-block text-sm text-principal underline"
          >
            Voltar ao guia
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-fundo">
      <CabecalhoEnxoval enxoval={enxoval} abaAtiva="guia" />

      <main className="mx-auto max-w-3xl space-y-5 px-4 py-6 sm:px-6 sm:py-8">
        {/* Cabeçalho */}
        <div>
          <Link
            to={`/enxoval/${id}/guia`}
            className="mb-2 inline-flex items-center gap-1 text-sm text-texto-suave hover:text-principal"
          >
            ← Guia dos itens
          </Link>
          <h1 className="font-titulo text-2xl font-semibold text-texto">
            {ficha.nome}
          </h1>
        </div>

        {/* Para que serve */}
        <section className="rounded-2xl bg-superficie p-4 shadow-sm">
          <h2 className="mb-2 font-semibold text-texto">Para que serve</h2>
          <p className="text-sm leading-relaxed text-texto">
            {ficha.para_que_serve}
          </p>
        </section>

        {/* Como escolher */}
        <section className="rounded-2xl bg-superficie p-4 shadow-sm">
          <h2 className="mb-2 font-semibold text-texto">Como escolher</h2>
          <p className="text-sm leading-relaxed text-texto">
            {ficha.como_escolher}
          </p>
        </section>

        {/* Marcas */}
        {ficha.marcas.nomes.length > 0 && (
          <section className="rounded-2xl bg-superficie p-4 shadow-sm">
            <h2 className="mb-2 font-semibold text-texto">
              Marcas
              {ficha.marcas.faixa && (
                <span className="ml-2 text-sm font-normal text-texto-suave">
                  {ficha.marcas.faixa_aproximada ? '(aproximado) ' : ''}
                  {ROTULOS_FAIXA[ficha.marcas.faixa] ?? ficha.marcas.faixa}
                </span>
              )}
            </h2>
            <ul className="flex flex-wrap gap-2">
              {ficha.marcas.nomes.map((nome) => (
                <li
                  key={nome}
                  className="rounded-xl bg-principal-suave px-3 py-1 text-sm text-texto"
                >
                  {nome}
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Dicas */}
        {ficha.dicas.length > 0 && (
          <section className="rounded-2xl bg-superficie p-4 shadow-sm">
            <h2 className="mb-2 font-semibold text-texto">Dicas</h2>
            <ul className="space-y-1">
              {ficha.dicas.map((dica, i) => (
                <li key={i} className="flex gap-2 text-sm text-texto">
                  <span className="text-principal" aria-hidden>
                    ·
                  </span>
                  {dica}
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Regras de segurança */}
        {ficha.regras_seguranca.length > 0 && (
          <section className="rounded-2xl bg-alerta-fundo p-4">
            <h2 className="mb-2 font-semibold text-alerta-texto">
              ⚠ Segurança
            </h2>
            <ul className="space-y-1">
              {ficha.regras_seguranca.map((regra, i) => (
                <li key={i} className="text-sm text-alerta-texto">
                  {regra}
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Aviso de conteúdo em validação */}
        <p className="text-xs text-texto-suave">
          Marcas e regras de segurança estão em processo de validação. Confirme
          com seu pediatra.
        </p>
      </main>
    </div>
  )
}
