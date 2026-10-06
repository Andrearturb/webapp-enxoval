import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AppRoutes } from './App'

function renderEm(caminho: string) {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[caminho]}>
        <AppRoutes />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('AppRoutes', () => {
  it.each([
    ['/', 'Início'],
    ['/questionario/1', 'Questionário'],
    ['/enxoval/abc123/planilha', 'Planilha'],
    ['/enxoval/abc123/roteiro', 'Roteiro'],
    ['/enxoval/abc123/guia', 'Guia dos itens'],
    ['/enxoval/abc123/guia/berco', 'Guia do item'],
    ['/enxoval/abc123/seguranca', 'Segurança'],
    ['/enxoval/abc123/ajustes', 'Ajustes'],
  ])('a rota %s mostra a página certa', (caminho, texto) => {
    renderEm(caminho)
    expect(screen.getByText(texto)).toBeInTheDocument()
  })

  it('uma rota desconhecida mostra a página de não encontrada, não tela branca', () => {
    renderEm('/isso-nao-existe')
    expect(screen.getByText('Página não encontrada')).toBeInTheDocument()
  })

  it('aceita qualquer valor de :id e :item na rota de guia do item', () => {
    renderEm('/enxoval/qualquer-coisa/guia/qualquer-item')
    expect(screen.getByText('Guia do item')).toBeInTheDocument()
  })
})
