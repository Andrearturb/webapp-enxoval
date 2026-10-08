import { StrictMode } from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('keycloak-js', () => ({
  default: class {
    token = 'token'
    tokenParsed = { preferred_username: 'familia' }
    init = vi.fn().mockResolvedValue(true)
    updateToken = vi.fn().mockResolvedValue(false)
    logout = vi.fn()
  },
}))

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_KEYCLOAK_HABILITADO', 'true')
  })

  it('inicializa uma única vez sob StrictMode e aguarda o login', async () => {
    // A flag é lida na importação; recarregamos os módulos com o ambiente de auth.
    vi.resetModules()
    const { AuthProvider: Provider } = await import('./AuthProvider')
    const { keycloak: adapter } = await import('./keycloak')
    render(<StrictMode><Provider><p>Conteúdo protegido</p></Provider></StrictMode>)
    await waitFor(() => expect(screen.getByText('Conteúdo protegido')).toBeInTheDocument())
    expect(adapter.init).toHaveBeenCalledOnce()
    vi.unstubAllEnvs()
  })

  it('bloqueia o conteúdo quando o servidor de autenticação falha', async () => {
    vi.resetModules()
    const { AuthProvider: Provider } = await import('./AuthProvider')
    const { keycloak: adapter } = await import('./keycloak')
    vi.mocked(adapter.init).mockRejectedValue(new Error('indisponível'))
    render(<Provider><p>Conteúdo protegido</p></Provider>)
    expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível autenticar')
    expect(screen.queryByText('Conteúdo protegido')).not.toBeInTheDocument()
    vi.unstubAllEnvs()
  })

  it('usa a raiz com barra final no retorno do logout permitido pelo realm', async () => {
    vi.resetModules()
    const { AuthProvider: Provider, useAuth } = await import('./AuthProvider')
    const { keycloak: adapter } = await import('./keycloak')
    function Conta() {
      const { sair } = useAuth()
      return <button onClick={sair}>Sair</button>
    }
    render(<Provider><Conta /></Provider>)
    fireEvent.click(await screen.findByRole('button', { name: 'Sair' }))
    expect(adapter.logout).toHaveBeenCalledWith({ redirectUri: `${window.location.origin}/` })
    vi.unstubAllEnvs()
  })
})
