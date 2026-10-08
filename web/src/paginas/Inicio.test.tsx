import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import Inicio from './Inicio'

function renderInicio() {
  render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<Inicio />} />
        <Route path="/questionario/1" element={<p>Questionario passo 1</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('Inicio', () => {
  it('mostra a proposta do produto', () => {
    renderInicio()
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
    expect(screen.getByText(/enxoval certo/i)).toBeInTheDocument()
  })

  it('tem pelo menos um link para começar o enxoval', () => {
    renderInicio()
    const links = screen.getAllByRole('link', { name: /começar/i })
    expect(links.length).toBeGreaterThan(0)
    expect(links[0]).toHaveAttribute('href', '/questionario/1')
  })

  it('link começar navega para o questionário', () => {
    renderInicio()
    // Clica no primeiro link de "Começar"
    fireEvent.click(screen.getAllByRole('link', { name: /começar/i })[0])
    expect(screen.getByText('Questionario passo 1')).toBeInTheDocument()
  })

  it('mostra os passos de como funciona', () => {
    renderInicio()
    expect(screen.getByRole('heading', { name: 'Como funciona' })).toBeInTheDocument()
    expect(screen.getByText('Responda 6 perguntas')).toBeInTheDocument()
  })
})
