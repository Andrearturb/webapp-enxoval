import { describe, expect, it, vi } from 'vitest'
import { apiFetch } from './cliente'
import { criarEnxoval } from './enxovais'

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
