import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { beforeAll, describe, expect, it, vi } from 'vitest'
import { keycloak } from '../auth/keycloak'
import { getPerfil, salvarAvatar } from '../api/perfil'
import MinhaConta from './MinhaConta'

vi.mock('../auth/keycloak', () => ({
  keycloakHabilitado: true,
  keycloak: {
    subject: 'usuario-123',
    updateToken: vi.fn().mockResolvedValue(false),
    login: vi.fn().mockResolvedValue(undefined),
    loadUserProfile: vi
      .fn()
      .mockResolvedValue({
        firstName: 'Ana',
        lastName: 'Silva',
        email: 'ana@example.com',
        emailVerified: true,
      }),
  },
}))
vi.mock('../auth/AuthProvider', () => ({
  useAuth: () => ({ nomeUsuario: 'Ana', sair: vi.fn() }),
}))
vi.mock('../api/perfil', () => ({
  getPerfil: vi.fn(),
  salvarAvatar: vi.fn(),
}))

beforeAll(() => {
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', '') }
  HTMLDialogElement.prototype.close = function () { this.removeAttribute('open') }
})
function abrir() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <MinhaConta />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Minha conta', () => {
  it('mostra dados verificados e abre a edição de nome no Keycloak', async () => {
    vi.mocked(getPerfil).mockResolvedValue({ avatar: 'ursinho' })
    abrir()
    expect(await screen.findByText('ana@example.com')).toBeInTheDocument()
    expect(screen.getByText('Ana Silva')).toBeInTheDocument()
    expect(screen.getByText('E-mail verificado')).toBeInTheDocument()
    fireEvent.click(
      screen.getByRole('button', { name: 'Editar dados pessoais' }),
    )
    expect(keycloak.login).toHaveBeenCalledWith({
      action: 'UPDATE_PROFILE',
      redirectUri: `${window.location.origin}/minha-conta`,
    })
  })
  it('mostra só o avatar atual e salva a escolha feita no modal', async () => {
    vi.mocked(getPerfil).mockResolvedValue({ avatar: 'lua' })
    vi.mocked(salvarAvatar).mockResolvedValue({ avatar: 'coelhinho' })
    abrir()
    const abrirModal = screen.getByRole('button', { name: 'Alterar avatar' })
    await waitFor(() => expect(abrirModal).toBeEnabled())
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Escolher Coelhinho' })).not.toBeInTheDocument()
    fireEvent.click(abrirModal)
    const modal = screen.getByRole('dialog', { name: 'Escolha seu avatar' })
    expect(within(modal).getAllByRole('button', { name: /^Escolher / })).toHaveLength(6)
    fireEvent.click(within(modal).getByRole('button', { name: 'Escolher Coelhinho' }))
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Avatar atualizado.'))
    expect(salvarAvatar).toHaveBeenCalledWith('coelhinho', expect.anything())
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(abrirModal.querySelector('img')).toHaveAttribute('src', '/avatares/coelhinho.webp')
    expect(document.querySelector('input[type="file"]')).toBeNull()
    expect(screen.queryByRole('button', { name: 'Usar minhas iniciais' })).not.toBeInTheDocument()
  })
  it('mantém o modal aberto e a escolha anterior quando salvar falha', async () => {
    vi.mocked(getPerfil).mockResolvedValue({ avatar: 'lua' })
    vi.mocked(salvarAvatar).mockRejectedValue(new Error('Falha de conexão'))
    abrir()
    const abrirModal = screen.getByRole('button', { name: 'Alterar avatar' })
    await waitFor(() => expect(abrirModal).toBeEnabled())
    fireEvent.click(abrirModal)
    fireEvent.click(screen.getByRole('button', { name: 'Escolher Patinho' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível atualizar seu avatar.')
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Escolher Lua' })).toHaveAttribute('aria-pressed', 'true')
  })
  it('fecha pelo botão ou Escape sem alterar a escolha', async () => {
    vi.mocked(getPerfil).mockResolvedValue({ avatar: 'lua' })
    abrir()
    const abrirModal = screen.getByRole('button', { name: 'Alterar avatar' })
    await waitFor(() => expect(abrirModal).toBeEnabled())
    fireEvent.click(abrirModal)
    fireEvent.click(screen.getByRole('button', { name: 'Fechar seleção de avatar' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    fireEvent.click(abrirModal)
    fireEvent(screen.getByRole('dialog'), new Event('cancel', { bubbles: false, cancelable: true }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(salvarAvatar).not.toHaveBeenCalled()
    expect(abrirModal.querySelector('img')).toHaveAttribute('src', '/avatares/lua.webp')
  })
})
