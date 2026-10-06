import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PassoFrequenciaLavagem from './PassoFrequenciaLavagem'

describe('PassoFrequenciaLavagem', () => {
  it('converte a opção escolhida em dias_entre_lavagens', () => {
    const onChange = vi.fn()
    render(<PassoFrequenciaLavagem respostas={{}} onChange={onChange} />)

    fireEvent.click(screen.getByText('Lavo a cada 2 dias'))

    expect(onChange).toHaveBeenCalledWith({ dias_entre_lavagens: 2 })
  })

  it('marca a opção já escolhida ao reabrir o passo', () => {
    render(
      <PassoFrequenciaLavagem respostas={{ dias_entre_lavagens: 3 }} onChange={vi.fn()} />,
    )
    expect(screen.getByText('Lavo a cada 3 dias')).toHaveAttribute('aria-checked', 'true')
  })
})
