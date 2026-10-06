import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PassoDataPrevista from './PassoDataPrevista'

describe('PassoDataPrevista', () => {
  it('chama onChange com a data escolhida', () => {
    const onChange = vi.fn()
    render(<PassoDataPrevista respostas={{}} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText('Data prevista'), {
      target: { value: '2027-06-15' },
    })

    expect(onChange).toHaveBeenCalledWith({ data_prevista: '2027-06-15' })
  })

  it('mostra a data já escolhida ao reabrir o passo', () => {
    render(<PassoDataPrevista respostas={{ data_prevista: '2027-06-15' }} onChange={vi.fn()} />)
    expect(screen.getByLabelText('Data prevista')).toHaveValue('2027-06-15')
  })
})
