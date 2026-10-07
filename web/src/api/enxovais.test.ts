import { describe, expect, it, vi } from 'vitest'
import { apiFetch } from './cliente'
import { criarEnxoval, getEnxoval, marcarLinha, completarLinha } from './enxovais'

vi.mock('./cliente', () => ({ apiFetch: vi.fn() }))

describe('criarEnxoval', () => {
  it('faz POST para /enxovais com o corpo em JSON', async () => {
    vi.mocked(apiFetch).mockResolvedValue({ id: 'abc' })
    const dados = {
      municipio_codigo: 1,
      data_prevista: '2027-06-15',
      dias_entre_lavagens: 2,
      moradia: 'apartamento' as const,
      tem_carro: true,
      orcamento: 'intermediario' as const,
      primeiro_filho: true,
    }
    await criarEnxoval(dados)
    expect(apiFetch).toHaveBeenCalledWith('/enxovais', {
      method: 'POST',
      body: JSON.stringify(dados),
    })
  })
})

describe('getEnxoval', () => {
  it('faz GET para /enxovais/{id}', async () => {
    vi.mocked(apiFetch).mockResolvedValue({ id: 'abc', linhas: [] })
    await getEnxoval('abc')
    expect(apiFetch).toHaveBeenCalledWith('/enxovais/abc')
  })
})

describe('marcarLinha', () => {
  it('faz PUT para /enxovais/{id}/linhas/{chave} com comprada/ganhada/ja_tinha', async () => {
    vi.mocked(apiFetch).mockResolvedValue({})
    await marcarLinha('abc', 'body:P:', { comprada: 2, ganhada: 1, ja_tinha: 0 })
    expect(apiFetch).toHaveBeenCalledWith('/enxovais/abc/linhas/body%3AP%3A', {
      method: 'PUT',
      body: JSON.stringify({ comprada: 2, ganhada: 1, ja_tinha: 0 }),
    })
  })
})

describe('completarLinha', () => {
  it('faz POST para /enxovais/{id}/linhas/{chave}/completar com a origem', async () => {
    vi.mocked(apiFetch).mockResolvedValue({})
    await completarLinha('abc', 'body:P:', 'comprada')
    expect(apiFetch).toHaveBeenCalledWith('/enxovais/abc/linhas/body%3AP%3A/completar', {
      method: 'POST',
      body: JSON.stringify({ origem: 'comprada' }),
    })
  })
})
