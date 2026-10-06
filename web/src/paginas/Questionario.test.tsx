import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { buscarMunicipios } from '../api/municipios'
import Questionario from './Questionario'

vi.mock('../api/municipios')
vi.mock('../api/enxovais')

function renderEm(caminho: string) {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[caminho]}>
        <Routes>
          <Route path="/questionario/:passo" element={<Questionario />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Questionario', () => {
  it('mostra o passo 1 por padrão e desabilita Voltar', () => {
    renderEm('/questionario/1')
    expect(screen.getByText('Passo 1 de 6')).toBeInTheDocument()
    expect(screen.getByText('Voltar')).toBeDisabled()
  })

  it.each(['/questionario/0', '/questionario/99', '/questionario/abc'])(
    '%s cai no passo 1 em vez de tela branca',
    (caminho) => {
      renderEm(caminho)
      expect(screen.getByText('Passo 1 de 6')).toBeInTheDocument()
    },
  )

  it('Avançar fica desabilitado até escolher uma cidade, e habilita depois', async () => {
    vi.mocked(buscarMunicipios).mockResolvedValue([
      { codigo_ibge: 4106902, nome: 'Curitiba', uf: 'PR', perfil_sugerido: 'frio' },
    ])
    renderEm('/questionario/1')
    expect(screen.getByText('Avançar')).toBeDisabled()

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'curitiba' } })
    await waitFor(() => screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Curitiba - PR'))

    expect(screen.getByText('Avançar')).toBeEnabled()
  })

  it('preserva a cidade escolhida ao avançar e voltar', async () => {
    vi.mocked(buscarMunicipios).mockResolvedValue([
      { codigo_ibge: 4106902, nome: 'Curitiba', uf: 'PR', perfil_sugerido: 'frio' },
    ])
    renderEm('/questionario/1')

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'curitiba' } })
    await waitFor(() => screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Avançar'))

    expect(screen.getByText('Passo 2 de 6')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Voltar'))

    expect(screen.getByDisplayValue('Curitiba - PR')).toBeInTheDocument()
  })
})
