/**
 * Tela "Meus enxovais" — ponto de entrada após o login.
 *
 * Lista todos os enxovais do usuário logado com cidade, data prevista
 * e progresso. Permite criar um novo enxoval ou abrir um existente.
 */
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { listarEnxovais, type EnxovalResumo } from '../api/enxovais'
import { useAuth } from '../auth/AuthProvider'
import { Marca } from '../componentes/Marca'
import {
  ArrowRight,
  CalendarDays,
  Plus,
  ShoppingBag,
} from 'lucide-react'
import { IlustracaoEnxoval } from '../componentes/IlustracaoEnxoval'
import { MinhaContaLink } from '../componentes/MinhaContaLink'

function formatarData(dataStr: string): string {
  return new Date(dataStr + 'T12:00:00').toLocaleDateString('pt-BR', {
    month: 'long',
    year: 'numeric',
  })
}

function CardEnxoval({ enxoval }: { enxoval: EnxovalResumo }) {
  return (
    <Link
      to={`/enxoval/${enxoval.id}/planilha`}
      className="group block rounded-3xl border border-borda bg-superficie p-5 transition-all hover:border-principal/40 hover:shadow-sm sm:p-6"
    >
      <div className="mb-5 flex items-center justify-between">
        <span className="flex size-11 items-center justify-center rounded-2xl bg-principal-suave text-principal">
          <ShoppingBag size={20} aria-hidden="true" />
        </span>
        <ArrowRight
          size={18}
          className="text-principal transition-transform group-hover:translate-x-1"
          aria-hidden="true"
        />
      </div>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-titulo text-xl font-semibold text-texto">
            {enxoval.municipio_nome} — {enxoval.municipio_uf}
          </p>
          <p className="mt-2 flex items-center gap-1.5 text-xs text-texto-suave">
            <CalendarDays size={14} aria-hidden="true" />
            Previsão: {formatarData(enxoval.data_prevista)}
          </p>
        </div>
        {/* Progresso */}
        <span
          className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${
            enxoval.percentual_progresso >= 80
              ? 'bg-[#E1EAE2] text-[#36513D]'
              : enxoval.percentual_progresso >= 40
                ? 'bg-principal-suave text-principal'
                : 'bg-principal-suave text-principal'
          }`}
        >
          {enxoval.percentual_progresso}%
        </span>
      </div>

      {/* Barra de progresso */}
      <div
        className="mt-5 h-1.5 w-full overflow-hidden rounded-full bg-principal-suave"
        role="progressbar"
        aria-valuenow={enxoval.percentual_progresso}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Progresso: ${enxoval.percentual_progresso}%`}
      >
        <div
          className="h-full rounded-full bg-principal transition-all"
          style={{ width: `${enxoval.percentual_progresso}%` }}
        />
      </div>
      <p className="mt-2 text-xs text-texto-suave">
        {enxoval.percentual_progresso === 100
          ? 'Tudo organizado para esta fase'
          : 'Cada item, uma pequena conquista'}
      </p>
    </Link>
  )
}

export default function MeusEnxovais() {
  const { nomeUsuario } = useAuth()

  const {
    data: enxovais,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['meus-enxovais'],
    queryFn: listarEnxovais,
  })

  return (
    <div className="min-h-screen bg-fundo">
      {/* Cabeçalho simples */}
      <header className="border-b border-borda bg-superficie">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-5 py-4 sm:px-6">
          <Marca destino="/meus-enxovais" />
          {nomeUsuario && (
            <div className="flex items-center gap-3">
              <span className="hidden max-w-48 truncate text-sm text-texto-suave sm:inline">
                {nomeUsuario}
              </span>
              <MinhaContaLink />
            </div>
          )}
        </div>
      </header>

      <main className="mx-auto min-h-[65vh] max-w-5xl space-y-7 px-5 py-8 sm:px-6 sm:py-12">
        <div className="flex flex-wrap items-end justify-between gap-5">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-[.16em] text-principal">
              Um começo cheio de cuidado
            </p>
            <h1 className="font-titulo text-3xl font-semibold text-texto sm:text-4xl">
              Meus enxovais
            </h1>
            <p className="mt-3 max-w-md text-sm leading-relaxed text-texto-suave">
              Sua lista, suas conquistas e os próximos passos. Tudo em um lugar.
            </p>
          </div>
          <Link
            to="/questionario/1"
            className="inline-flex min-h-12 items-center gap-2 rounded-2xl bg-principal px-5 py-3 text-sm font-medium text-white hover:bg-principal/90"
          >
            <Plus size={17} aria-hidden="true" /> Novo enxoval
          </Link>
        </div>

        {isLoading && (
          <p className="py-8 text-center text-texto-suave">Carregando...</p>
        )}

        {isError && (
          <p
            role="alert"
            className="rounded-2xl bg-alerta-fundo p-4 text-alerta-texto"
          >
            Não foi possível carregar seus enxovais. Tente de novo.
          </p>
        )}

        {enxovais && enxovais.length === 0 && (
          <div className="rounded-3xl border border-borda bg-superficie px-5 pb-10 pt-5 text-center">
            <IlustracaoEnxoval className="mx-auto w-56" />
            <h2 className="text-2xl font-semibold">
              Vamos preparar esse começo?
            </h2>
            <p className="mx-auto mt-3 max-w-sm text-sm leading-relaxed text-texto-suave">
              Você ainda não tem nenhum enxoval. Responda algumas perguntas e
              descubra o que faz sentido para sua família.
            </p>
            <Link
              to="/questionario/1"
              className="mt-4 inline-block rounded-xl bg-principal px-6 py-3 font-medium text-white hover:opacity-90"
            >
              Criar meu primeiro enxoval
            </Link>
          </div>
        )}

        {enxovais && enxovais.length > 0 && (
          <ul className="grid gap-4 md:grid-cols-2" role="list">
            {enxovais.map((enxoval) => (
              <li key={enxoval.id}>
                <CardEnxoval enxoval={enxoval} />
              </li>
            ))}
          </ul>
        )}
      </main>

      <footer className="border-t border-borda px-4 py-6 text-center">
        <p className="text-xs text-texto-suave">
          Marcas e regras de segurança em processo de validação. Confirme com
          seu pediatra.
        </p>
      </footer>
    </div>
  )
}
