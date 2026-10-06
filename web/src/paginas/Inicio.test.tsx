import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Inicio from './Inicio'

describe('Inicio', () => {
  it('mostra o título da página', () => {
    render(<Inicio />)
    expect(screen.getByText('Início')).toBeInTheDocument()
  })
})
