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
      className="block rounded-2xl bg-superficie p-5 shadow-sm transition-shadow hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-texto">
            {enxoval.municipio_nome} — {enxoval.municipio_uf}
          </p>
          <p className="mt-0.5 text-sm text-texto-suave">
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
                : 'bg-alerta-fundo text-alerta-texto'
          }`}
        >
          {enxoval.percentual_progresso}%
        </span>
      </div>

      {/* Barra de progresso */}
      <div
        className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-principal-suave"
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
    </Link>
  )
}

export default function MeusEnxovais() {
  const { nomeUsuario, sair } = useAuth()

  const { data: enxovais, isLoading, isError } = useQuery({
    queryKey: ['meus-enxovais'],
    queryFn: listarEnxovais,
  })

  return (
    <div className="min-h-screen bg-fundo">
      {/* Cabeçalho simples */}
      <header className="bg-superficie shadow-sm">
        <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-3">
          <h1 className="font-titulo font-semibold text-texto">Enxoval Inteligente</h1>
          {nomeUsuario && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-texto-suave">{nomeUsuario}</span>
              <button
                type="button"
                onClick={sair}
                className="text-sm text-texto-suave underline hover:text-principal"
              >
                Sair
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-2xl space-y-5 px-4 py-6">
        <div className="flex items-center justify-between">
          <h2 className="font-titulo text-xl font-semibold text-texto">Meus enxovais</h2>
          <Link
            to="/questionario/1"
            className="rounded-xl bg-principal px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90"
          >
            + Novo enxoval
          </Link>
        </div>

        {isLoading && (
          <p className="py-8 text-center text-texto-suave">Carregando...</p>
        )}

        {isError && (
          <p role="alert" className="rounded-2xl bg-alerta-fundo p-4 text-alerta-texto">
            Não foi possível carregar seus enxovais. Tente de novo.
          </p>
        )}

        {enxovais && enxovais.length === 0 && (
          <div className="rounded-2xl bg-superficie p-8 text-center shadow-sm">
            <p className="text-texto-suave">Você ainda não tem nenhum enxoval.</p>
            <Link
              to="/questionario/1"
              className="mt-4 inline-block rounded-xl bg-principal px-6 py-3 font-medium text-white hover:opacity-90"
            >
              Criar meu primeiro enxoval
            </Link>
          </div>
        )}

        {enxovais && enxovais.length > 0 && (
          <ul className="space-y-3" role="list">
            {enxovais.map((enxoval) => (
              <li key={enxoval.id}>
                <CardEnxoval enxoval={enxoval} />
              </li>
            ))}
          </ul>
        )}
      </main>

      <footer className="border-t border-principal-suave px-4 py-6 text-center">
        <p className="text-xs text-texto-suave">
          Marcas e regras de segurança em processo de validação. Confirme com seu pediatra.
        </p>
      </footer>
    </div>
  )
}
