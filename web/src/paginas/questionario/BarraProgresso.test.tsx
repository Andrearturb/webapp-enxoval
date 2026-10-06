import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { BarraProgresso } from './BarraProgresso'

describe('BarraProgresso', () => {
  it('mostra o passo atual e o total', () => {
    render(<BarraProgresso passo={2} total={6} />)
    expect(screen.getByText('Passo 2 de 6')).toBeInTheDocument()
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '2')
  })
})
