import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AppRoutes } from './App'

// A rota de planilha faz uma query real; mockamos para mantê-la no estado de loading
vi.mock('./api/enxovais', async (importOriginal) => {
  const mod = await importOriginal<typeof import('./api/enxovais')>()
  return {
    ...mod,
    getEnxoval: vi.fn(() => new Promise(() => {})),
  }
})

function renderEm(caminho: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[caminho]}>
        <AppRoutes />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('AppRoutes', () => {
  // Rotas que dependem de getEnxoval ficam no estado "Carregando..." (getEnxoval mockado com promise pendente)
  it.each([
    ['/', 'Início'],
    ['/questionario/1', 'Questionário'],
    ['/enxoval/abc123/planilha', 'Carregando'],
    ['/enxoval/abc123/roteiro', 'Carregando'],
    ['/enxoval/abc123/guia', 'Carregando'],
    ['/enxoval/abc123/guia/berco', 'Carregando'],
    ['/enxoval/abc123/seguranca', 'Carregando'],
    ['/enxoval/abc123/ajustes', 'Ajustes'],
  ])('a rota %s mostra a página certa', (caminho, texto) => {
    renderEm(caminho)
    expect(screen.getByText(new RegExp(texto, 'i'))).toBeInTheDocument()
  })

  it('uma rota desconhecida mostra a página de não encontrada, não tela branca', () => {
    renderEm('/isso-nao-existe')
    expect(screen.getByText('Página não encontrada')).toBeInTheDocument()
  })

  it('aceita qualquer valor de :id e :item na rota de guia do item', () => {
    renderEm('/enxoval/qualquer-coisa/guia/qualquer-item')
    // GuiaItem usa usePlanilha → fica em loading com getEnxoval mockado como pendente
    expect(screen.getByText(/carregando/i)).toBeInTheDocument()
  })
})
