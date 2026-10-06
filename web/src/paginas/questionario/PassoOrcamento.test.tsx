import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PassoOrcamento from './PassoOrcamento'

describe('PassoOrcamento', () => {
  it('registra a faixa de orçamento escolhida', () => {
    const onChange = vi.fn()
    render(<PassoOrcamento respostas={{}} onChange={onChange} />)

    fireEvent.click(screen.getByText('Investir mais'))

    expect(onChange).toHaveBeenCalledWith({ orcamento: 'investir' })
  })
})
