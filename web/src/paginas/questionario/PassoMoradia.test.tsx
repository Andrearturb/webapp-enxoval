import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PassoMoradia from './PassoMoradia'

describe('PassoMoradia', () => {
  it('registra moradia e carro separadamente', () => {
    const onChange = vi.fn()
    render(<PassoMoradia respostas={{}} onChange={onChange} />)

    fireEvent.click(screen.getByText('Casa com escada'))
    expect(onChange).toHaveBeenCalledWith({ moradia: 'casa_com_escada' })

    fireEvent.click(screen.getByText('Sim'))
    expect(onChange).toHaveBeenCalledWith({ tem_carro: true })
  })

  it('mostra Não para tem_carro quando a resposta já é falsa', () => {
    render(<PassoMoradia respostas={{ tem_carro: false }} onChange={vi.fn()} />)
    expect(screen.getByText('Não')).toHaveAttribute('aria-checked', 'true')
  })
})
