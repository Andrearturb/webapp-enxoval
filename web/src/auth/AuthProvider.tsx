/**
 * AuthProvider — inicializa o Keycloak e fornece o token via Context.
 *
 * Comportamento:
 * - KEYCLOAK_HABILITADO=false (dev): renderiza filhos diretamente sem
 *   autenticação. Token é undefined; apiFetch não envia Authorization.
 * - KEYCLOAK_HABILITADO=true: inicializa com `login-required` — redireciona
 *   para a tela de login do Keycloak se o usuário não estiver autenticado.
 *   Refresca o token automaticamente a cada 4 minutos (token expira em 5).
 */
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import { inicializarKeycloak, keycloak, keycloakHabilitado } from './keycloak'

interface AuthContextValue {
  /** Token de acesso atual (Bearer). Undefined se auth desabilitada. */
  token: string | undefined
  /** Nome exibido do usuário logado. Undefined se auth desabilitada. */
  nomeUsuario: string | undefined
  /** Desloga o usuário e redireciona para o Keycloak. */
  sair: () => void
}

const AuthContext = createContext<AuthContextValue>({
  token: undefined,
  nomeUsuario: undefined,
  sair: () => {},
})

export function useAuth(): AuthContextValue {
  return useContext(AuthContext)
}

interface Props {
  children: ReactNode
}

export function AuthProvider({ children }: Props) {
  const [pronto, setPronto] = useState(!keycloakHabilitado)
  const [token, setToken] = useState<string | undefined>(undefined)
  const [nomeUsuario, setNomeUsuario] = useState<string | undefined>(undefined)
  const [erro, setErro] = useState(false)

  useEffect(() => {
    if (!keycloakHabilitado) return

    let ativo = true
    let intervalo: ReturnType<typeof setInterval> | undefined
    inicializarKeycloak()
      .then((autenticado) => {
        if (!ativo) return
        if (autenticado) {
          if (keycloak.tokenParsed?.['email_verified'] !== true) {
            void keycloak
              .login({
                action: 'VERIFY_EMAIL',
                redirectUri: window.location.href,
              })
              .catch(() => {
                if (ativo) setErro(true)
              })
            return
          }
          setToken(keycloak.token)
          setNomeUsuario(
            keycloak.tokenParsed?.['name'] ??
              keycloak.tokenParsed?.['preferred_username'] ??
              keycloak.tokenParsed?.['email'],
          )
          setPronto(true)

          // Refresca o token 1 minuto antes de expirar (token dura 5 min)
          intervalo = setInterval(
            () => {
              keycloak
                .updateToken(60)
                .then((renovado) => {
                  if (ativo && renovado) setToken(keycloak.token)
                })
                .catch(() => {
                  if (ativo) setErro(true)
                })
            },
            4 * 60 * 1000,
          )
        } else {
          setErro(true)
        }
      })
      .catch(() => {
        if (ativo) setErro(true)
      })
    return () => {
      ativo = false
      if (intervalo) clearInterval(intervalo)
    }
  }, [])

  function sair() {
    if (keycloakHabilitado) {
      keycloak.logout({ redirectUri: `${window.location.origin}/` })
    }
  }

  if (erro) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-fundo">
        <p role="alert">Não foi possível autenticar. Tente entrar novamente.</p>
        <button type="button" onClick={() => window.location.reload()}>
          Tentar novamente
        </button>
      </div>
    )
  }

  if (!pronto) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-fundo">
        <p className="text-texto-suave">Carregando...</p>
      </div>
    )
  }

  return (
    <AuthContext.Provider value={{ token, nomeUsuario, sair }}>
      {children}
    </AuthContext.Provider>
  )
}
