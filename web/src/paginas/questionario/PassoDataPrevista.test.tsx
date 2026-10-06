import { useState } from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { RespostasParciais } from './tipos'
import PassoDataPrevista from './PassoDataPrevista'

function renderPasso(respostasIniciais: RespostasParciais = {}) {
  const onChange = vi.fn()

  function Harness() {
    const [respostas, setRespostas] = useState(respostasIniciais)
    function aoMudar(parcial: Partial<RespostasParciais>) {
      onChange(parcial)
      setRespostas((atual) => ({ ...atual, ...parcial }))
    }
    return <PassoDataPrevista respostas={respostas} onChange={aoMudar} />
  }

  render(<Harness />)
  return { onChange }
}

describe('PassoDataPrevista', () => {
  it('chama onChange com a data escolhida', () => {
    const { onChange } = renderPasso()

    fireEvent.change(screen.getByLabelText('Data prevista'), {
      target: { value: '2027-06-15' },
    })

    expect(onChange).toHaveBeenCalledWith({ data_prevista: '2027-06-15' })
  })

  it('mostra a data já escolhida ao reabrir o passo', () => {
    renderPasso({ data_prevista: '2027-06-15' })
    expect(screen.getByLabelText('Data prevista')).toHaveValue('2027-06-15')
  })
})

describe('PassoDataPrevista - validação de intervalo', () => {
  it('tem atributos min e max no input de data', () => {
    renderPasso()
    const input = screen.getByLabelText('Data prevista')
    expect(input).toHaveAttribute('min')
    expect(input).toHaveAttribute('max')
  })

  it('mostra mensagem de erro quando a data está fora do intervalo', () => {
    renderPasso()

    const muitoDepois = new Date()
    muitoDepois.setMonth(muitoDepois.getMonth() + 12)
    const dataForaDoIntervalo = muitoDepois.toISOString().slice(0, 10)

    fireEvent.change(screen.getByLabelText('Data prevista'), {
      target: { value: dataForaDoIntervalo },
    })

    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent(/data prevista/i)
  })

  it('não mostra mensagem de erro quando a data está dentro do intervalo', () => {
    renderPasso()

    const dentroDoIntervalo = new Date()
    dentroDoIntervalo.setMonth(dentroDoIntervalo.getMonth() + 5)
    const dataValida = dentroDoIntervalo.toISOString().slice(0, 10)

    fireEvent.change(screen.getByLabelText('Data prevista'), {
      target: { value: dataValida },
    })

    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
