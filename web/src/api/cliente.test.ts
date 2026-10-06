import { afterEach, describe, expect, it, vi } from 'vitest'
import { apiFetch, ErroApi } from './cliente'

describe('apiFetch', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('devolve o JSON da resposta quando a chamada dá certo', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ ok: true }),
      }),
    )
    await expect(apiFetch('/saude')).resolves.toEqual({ ok: true })
  })

  it('lança ErroApi com o código e a mensagem do corpo quando a resposta não é ok', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        json: async () => ({ erro: 'dados_invalidos', mensagem: 'Confira os dados.' }),
      }),
    )
    await expect(apiFetch('/enxovais')).rejects.toMatchObject({
      codigo: 'dados_invalidos',
      message: 'Confira os dados.',
      status: 422,
    })
  })

  it('lança ErroApi de sem_conexao quando o fetch falha', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('network')))
    await expect(apiFetch('/saude')).rejects.toMatchObject({ codigo: 'sem_conexao' })
    await expect(apiFetch('/saude')).rejects.toBeInstanceOf(ErroApi)
  })
})
