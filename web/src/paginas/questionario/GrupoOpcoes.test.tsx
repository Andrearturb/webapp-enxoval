import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { GrupoOpcoes } from './GrupoOpcoes'

const OPCOES = [
  { valor: 'a', rotulo: 'Opção A' },
  { valor: 'b', rotulo: 'Opção B' },
] as const

describe('GrupoOpcoes', () => {
  it('marca a opção escolhida e chama onEscolher ao clicar', () => {
    const onEscolher = vi.fn()
    render(<GrupoOpcoes nome="Teste" opcoes={OPCOES} valor="a" onEscolher={onEscolher} />)

    expect(screen.getByText('Opção A')).toHaveAttribute('aria-checked', 'true')
    expect(screen.getByText('Opção B')).toHaveAttribute('aria-checked', 'false')

    fireEvent.click(screen.getByText('Opção B'))
    expect(onEscolher).toHaveBeenCalledWith('b')
  })
})
