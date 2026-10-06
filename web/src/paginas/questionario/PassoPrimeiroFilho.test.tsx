import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PassoPrimeiroFilho from './PassoPrimeiroFilho'

describe('PassoPrimeiroFilho', () => {
  it('registra a resposta como booleano', () => {
    const onChange = vi.fn()
    render(<PassoPrimeiroFilho respostas={{}} onChange={onChange} />)

    fireEvent.click(screen.getByText('Não'))

    expect(onChange).toHaveBeenCalledWith({ primeiro_filho: false })
  })
})
