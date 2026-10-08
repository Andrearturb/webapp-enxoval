import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { keycloak } from '../auth/keycloak'
import { getPerfil, salvarFoto, removerFoto } from '../api/perfil'
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
  salvarFoto: vi.fn(),
  removerFoto: vi.fn(),
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
    vi.mocked(getPerfil).mockResolvedValue({ foto: null })
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
  it('envia e remove a foto, atualizando a página', async () => {
    vi.mocked(getPerfil).mockResolvedValue({ foto: null })
    vi.mocked(salvarFoto).mockResolvedValue({
      foto: 'data:image/jpeg;base64,abc',
    })
    vi.mocked(removerFoto).mockResolvedValue(undefined)
    abrir()
    await waitFor(() =>
      expect(screen.getByLabelText('Escolher foto')).toBeEnabled(),
    )
    const arquivo = new File(['foto'], 'foto.png', { type: 'image/png' })
    fireEvent.change(screen.getByLabelText('Escolher foto'), {
      target: { files: [arquivo] },
    })
    expect(await screen.findByRole('status')).toHaveTextContent(
      'Foto atualizada.',
    )
    expect(salvarFoto).toHaveBeenCalledWith(arquivo, expect.anything())
    fireEvent.click(screen.getByRole('button', { name: 'Remover foto' }))
    await waitFor(() =>
      expect(screen.getByRole('status')).toHaveTextContent('Foto removida.'),
    )
    expect(
      screen.queryByRole('button', { name: 'Remover foto' }),
    ).not.toBeInTheDocument()
  })
  it('rejeita arquivo grande antes de enviar', async () => {
    vi.mocked(getPerfil).mockResolvedValue({ foto: null })
    abrir()
    await waitFor(() =>
      expect(screen.getByLabelText('Escolher foto')).toBeEnabled(),
    )
    fireEvent.change(screen.getByLabelText('Escolher foto'), {
      target: {
        files: [
          new File([new Uint8Array(2 * 1024 * 1024 + 1)], 'grande.png', {
            type: 'image/png',
          }),
        ],
      },
    })
    expect(await screen.findByRole('alert')).toHaveTextContent('até 2 MB')
    expect(salvarFoto).not.toHaveBeenCalled()
  })
})
