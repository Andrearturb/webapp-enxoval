import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { keycloak } from '../auth/keycloak'
import { getPerfil, salvarAvatar, removerAvatar } from '../api/perfil'
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
  removerAvatar: vi.fn(),
}))

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
    vi.mocked(getPerfil).mockResolvedValue({ foto: null, avatar: null })
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
  it('escolhe um avatar e volta às iniciais', async () => {
    vi.mocked(getPerfil).mockResolvedValue({ foto: null, avatar: null })
    vi.mocked(salvarAvatar).mockResolvedValue({ foto: null, avatar: 'ursinho' })
    vi.mocked(removerAvatar).mockResolvedValue(undefined)
    abrir()
    const escolha = await screen.findByRole('button', { name: 'Escolher Ursinho' })
    await waitFor(() => expect(escolha).toBeEnabled())
    fireEvent.click(escolha)
    expect(await screen.findByRole('status')).toHaveTextContent('Avatar atualizado.')
    expect(salvarAvatar).toHaveBeenCalledWith('ursinho', expect.anything())
    expect(escolha).toHaveAttribute('aria-pressed', 'true')
    fireEvent.click(screen.getByRole('button', { name: 'Usar minhas iniciais' }))
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Seu perfil voltou a usar suas iniciais.'))
    expect(escolha).toHaveAttribute('aria-pressed', 'false')
    expect(screen.queryByRole('button', { name: 'Usar minhas iniciais' })).not.toBeInTheDocument()
  })
  it('mantém o avatar anterior quando a alteração falha', async () => {
    vi.mocked(getPerfil).mockResolvedValue({ foto: null, avatar: 'lua' })
    vi.mocked(salvarAvatar).mockRejectedValue(new Error('Falha de conexão'))
    abrir()
    const escolha = await screen.findByRole('button', { name: 'Escolher Patinho' })
    await waitFor(() => expect(escolha).toBeEnabled())
    fireEvent.click(escolha)
    expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível atualizar seu avatar.')
    expect(screen.getByRole('button', { name: 'Escolher Lua' })).toHaveAttribute('aria-pressed', 'true')
    expect(escolha).toHaveAttribute('aria-pressed', 'false')
  })
  it('mostra a foto antiga sem permitir novos uploads', async () => {
    vi.mocked(getPerfil).mockResolvedValue({ foto: 'data:image/jpeg;base64,abc', avatar: null })
    abrir()
    expect(await screen.findByText(/Você pode manter sua foto atual/)).toBeInTheDocument()
    expect(document.querySelector('input[type="file"]')).toBeNull()
    expect(screen.getAllByRole('button', { name: /^Escolher / })).toHaveLength(6)
  })
})