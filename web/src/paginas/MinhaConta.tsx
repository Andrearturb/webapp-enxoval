import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  BadgeCheck,
  KeyRound,
  LogOut,
  Pencil,
  Check,
} from 'lucide-react'
import { keycloak, keycloakHabilitado } from '../auth/keycloak'
import { useAuth } from '../auth/AuthProvider'
import { usePerfil } from '../hooks/usePerfil'
import { removerAvatar, salvarAvatar } from '../api/perfil'
import { AVATARES, imagemAvatar } from '../componentes/avatares'
import { ErroApi } from '../api/cliente'
import { Marca } from '../componentes/Marca'
import { AvatarUsuario } from '../componentes/MinhaContaLink'
import { Button } from '../componentes/ui/button'

export default function MinhaConta() {
  const { sair, nomeUsuario } = useAuth()
  const qc = useQueryClient()
  const perfil = usePerfil()
  const identidade = useQuery({
    queryKey: ['identidade', keycloak.subject],
    enabled: keycloakHabilitado,
    queryFn: async () => {
      await keycloak.updateToken(30)
      return keycloak.loadUserProfile()
    },
  })
  const [erro, setErro] = useState<string | null>(null)
  const [mensagem, setMensagem] = useState<string | null>(null)
  const [redirecionando, setRedirecionando] = useState(false)
  const avatar = useMutation({
    mutationFn: salvarAvatar,
    onSuccess: (novo) => {
      qc.setQueryData(['perfil', keycloak.subject], novo)
      setMensagem('Avatar atualizado.')
    },
    onError: (e) =>
      setErro(
        e instanceof ErroApi
          ? e.message
          : 'Não foi possível atualizar seu avatar.',
      ),
  })
  const remover = useMutation({
    mutationFn: removerAvatar,
    onSuccess: () => {
      qc.setQueryData(['perfil', keycloak.subject], { foto: null, avatar: null })
      setMensagem('Seu perfil voltou a usar suas iniciais.')
    },
    onError: (e) =>
      setErro(
        e instanceof ErroApi ? e.message : 'Não foi possível atualizar seu avatar.',
      ),
  })
  async function editar(action: 'UPDATE_PROFILE' | 'UPDATE_PASSWORD') {
    setErro(null)
    setRedirecionando(true)
    try {
      await keycloak.login({
        action,
        redirectUri: `${window.location.origin}/minha-conta`,
      })
    } catch {
      setErro('Não foi possível abrir a edição. Tente novamente.')
      setRedirecionando(false)
    }
  }
  const p = identidade.data
  const nome =
    [p?.firstName, p?.lastName].filter(Boolean).join(' ') ||
    nomeUsuario ||
    'Minha conta'
  const ocupado = avatar.isPending || remover.isPending

  return (
    <div className="min-h-screen bg-fundo">
      <header className="border-b border-borda bg-superficie">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-4 sm:px-6">
          <Marca destino="/meus-enxovais" />
          <Link
            to="/meus-enxovais"
            className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-borda px-3 text-sm text-principal"
          >
            <ArrowLeft size={16} aria-hidden="true" />
            Meus enxovais
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl space-y-5 px-4 py-7 sm:px-6 sm:py-10">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[.16em] text-principal">
            Seu espaço
          </p>
          <h1 className="mt-2 font-titulo text-3xl font-semibold">
            Minha conta
          </h1>
          <p className="mt-2 text-sm text-texto-suave">
            Cuide dos seus dados e deixe sua conta com a sua cara.
          </p>
        </div>
        {!keycloakHabilitado ? (
          <p>O perfil fica disponível quando o login está habilitado.</p>
        ) : (
          <>
            {erro && (
              <p
                role="alert"
                className="rounded-xl bg-alerta-fundo p-4 text-sm text-alerta-texto"
              >
                {erro}
              </p>
            )}
            {mensagem && (
              <p
                role="status"
                className="rounded-xl bg-principal-suave p-4 text-sm text-principal"
              >
                {mensagem}
              </p>
            )}
            <section
              aria-label="Avatar do perfil"
              aria-busy={ocupado}
              className="rounded-3xl border border-borda bg-superficie p-5 sm:p-6"
            >
              <div className="flex items-center gap-5">
                <AvatarUsuario avatar={perfil.data?.avatar} foto={perfil.data?.foto} nome={nome} grande />
                <div>
                  <h2 className="font-titulo text-xl font-semibold">
                    Seu avatar
                  </h2>
                  <p className="mt-2 text-sm text-texto-suave">
                    Escolha uma ilustração para acompanhar sua conta.
                  </p>
                </div>
              </div>
              {perfil.data?.foto && (
                <p className="mt-4 text-sm text-texto-suave">
                  Você pode manter sua foto atual ou escolher um dos avatares abaixo.
                </p>
              )}
              <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3" role="group" aria-label="Escolha seu avatar">
                {AVATARES.map(({ codigo, nome: rotulo }) => {
                  const selecionado = perfil.data?.avatar === codigo
                  return (
                    <button
                      key={codigo}
                      type="button"
                      aria-label={`Escolher ${rotulo}`}
                      aria-pressed={selecionado}
                      disabled={ocupado || perfil.isLoading || perfil.isError}
                      onClick={() => {
                        if (selecionado) return
                        setErro(null)
                        setMensagem(null)
                        avatar.mutate(codigo)
                      }}
                      className={`relative flex flex-col items-center gap-3 rounded-2xl border-2 px-3 py-4 transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-principal disabled:cursor-wait disabled:opacity-60 ${selecionado ? 'border-principal bg-principal-suave' : 'border-borda bg-fundo hover:border-principal/50'}`}
                    >
                      <img src={imagemAvatar(codigo)} alt="" width={96} height={96} className="size-20 rounded-full object-cover sm:size-24" />
                      <span className="text-sm font-medium text-texto">{rotulo}</span>
                      {selecionado && <Check size={16} aria-hidden="true" className="absolute right-2 top-2 text-principal" />}
                    </button>
                  )
                })}
              </div>
              {ocupado && <p className="mt-4 text-sm text-texto-suave">Atualizando seu avatar...</p>}
              {(perfil.data?.avatar || perfil.data?.foto) && (
                <Button
                  type="button"
                  variant="secundario"
                  className="mt-5"
                  disabled={ocupado || perfil.isError}
                  onClick={() => {
                    setErro(null)
                    setMensagem(null)
                    remover.mutate()
                  }}
                >
                  Usar minhas iniciais
                </Button>
              )}
              {perfil.isError && (
                <p role="alert" className="mt-3 text-sm text-alerta-texto">
                  Não foi possível carregar seu avatar.{' '}
                  <button
                    className="min-h-11 underline"
                    onClick={() => void perfil.refetch()}
                  >
                    Tentar novamente
                  </button>
                </p>
              )}
            </section>
            <section
              aria-label="Dados pessoais"
              className="rounded-3xl border border-borda bg-superficie p-5 sm:p-6"
            >
              <h2 className="font-titulo text-xl font-semibold">
                Dados pessoais
              </h2>
              {identidade.isLoading ? (
                <p className="mt-3 text-sm text-texto-suave">
                  Carregando seus dados...
                </p>
              ) : identidade.isError ? (
                <p role="alert" className="mt-3 text-sm text-alerta-texto">
                  Não foi possível carregar seus dados.{' '}
                  <button
                    className="min-h-11 underline"
                    onClick={() => void identidade.refetch()}
                  >
                    Tentar novamente
                  </button>
                </p>
              ) : (
                <dl className="mt-4 divide-y divide-borda text-sm">
                  <div className="space-y-1 py-3">
                    <dt className="text-texto-suave">Nome</dt>
                    <dd className="font-medium">{nome}</dd>
                  </div>
                  <div className="space-y-2 py-3">
                    <dt className="text-texto-suave">E-mail</dt>
                    <dd className="break-all font-medium">{p?.email}</dd>
                    <dd className="inline-flex items-center gap-1.5 rounded-full bg-principal-suave px-3 py-1 text-xs text-principal">
                      <BadgeCheck size={14} aria-hidden="true" />
                      {p?.emailVerified
                        ? 'E-mail verificado'
                        : 'Verificação pendente'}
                    </dd>
                  </div>
                </dl>
              )}
              <p className="my-4 text-sm text-texto-suave">
                Edite seu nome nos dados da conta. Se mudar o e-mail, será
                necessário confirmar o novo endereço.
              </p>
              <Button
                variant="secundario"
                disabled={redirecionando}
                onClick={() => void editar('UPDATE_PROFILE')}
              >
                <Pencil size={16} className="mr-2" aria-hidden="true" />
                Editar dados pessoais
              </Button>
            </section>
            <section
              aria-label="Segurança da conta"
              className="rounded-3xl border border-borda bg-superficie p-5 sm:p-6"
            >
              <h2 className="font-titulo text-xl font-semibold">
                Segurança da conta
              </h2>
              <p className="my-4 text-sm text-texto-suave">
                Atualize sua senha ou encerre sua sessão neste dispositivo.
              </p>
              <div className="flex flex-wrap gap-3">
                <Button
                  variant="secundario"
                  disabled={redirecionando}
                  onClick={() => void editar('UPDATE_PASSWORD')}
                >
                  <KeyRound size={16} className="mr-2" aria-hidden="true" />
                  Alterar senha
                </Button>
                <Button variant="secundario" onClick={sair}>
                  <LogOut size={16} className="mr-2" aria-hidden="true" />
                  Sair da conta
                </Button>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  )
}
