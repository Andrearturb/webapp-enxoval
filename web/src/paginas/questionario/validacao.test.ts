import { describe, expect, it } from 'vitest'
import { passoValido, todosPassosValidos } from './validacao'
import type { RespostasParciais } from './tipos'

const completas: RespostasParciais = {
  municipio_codigo: 4106902,
  data_prevista: '2027-06-15',
  dias_entre_lavagens: 2,
  moradia: 'apartamento',
  tem_carro: true,
  orcamento: 'intermediario',
  primeiro_filho: true,
}

describe('passoValido', () => {
  it.each([1, 2, 3, 4, 5, 6])(
    'passo %i é válido quando todas as respostas estão presentes',
    (passo) => {
      expect(passoValido(passo, completas)).toBe(true)
    },
  )

  it('passo 1 é inválido sem cidade', () => {
    expect(passoValido(1, {})).toBe(false)
  })

  it('passo 4 é inválido só com moradia, sem resposta sobre carro', () => {
    expect(passoValido(4, { moradia: 'apartamento' })).toBe(false)
  })

  it('passo fora do intervalo 1-6 é inválido', () => {
    expect(passoValido(0, completas)).toBe(false)
    expect(passoValido(7, completas)).toBe(false)
  })
})

describe('todosPassosValidos', () => {
  it('é verdadeiro só quando as 6 respostas estão completas', () => {
    expect(todosPassosValidos(completas)).toBe(true)
    expect(todosPassosValidos({ ...completas, primeiro_filho: undefined })).toBe(false)
  })
})
