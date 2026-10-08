import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { apiDownload, apiFetch, ErroApi } from './cliente'
import { keycloak } from '../auth/keycloak'

vi.mock('../auth/keycloak', () => ({
  keycloakHabilitado: true,
  keycloak: { token: 'token-teste', updateToken: vi.fn() },
}))

describe('apiFetch', () => {
  beforeEach(() => {
    vi.mocked(keycloak.updateToken).mockResolvedValue(false)
  })
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

  it('preserva headers personalizados e usa o token renovado', async () => {
    vi.mocked(keycloak.updateToken).mockImplementation(async () => {
      keycloak.token = 'token-renovado'
      return true
    })
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) })
    vi.stubGlobal('fetch', fetchMock)
    await apiFetch('/enxovais', { headers: new Headers({ 'X-Teste': 'sim' }) })
    const headers = fetchMock.mock.calls[0]![1].headers as Headers
    expect(headers.get('Authorization')).toBe('Bearer token-renovado')
    expect(headers.get('X-Teste')).toBe('sim')
    expect(headers.get('Content-Type')).toBe('application/json')
  })

  it('não envia requisição se a renovação da sessão falha', async () => {
    vi.mocked(keycloak.updateToken).mockRejectedValue(new Error('expirado'))
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    await expect(apiFetch('/enxovais')).rejects.toMatchObject({ codigo: 'sessao_expirada', status: 401 })
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('baixa arquivo com autorização e libera a URL temporária', async () => {
    vi.useFakeTimers()
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    const createObjectURL = vi.fn().mockReturnValue('blob:teste')
    const revokeObjectURL = vi.fn()
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL })
    const blob = new Blob(['lista'])
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, blob: async () => blob })
    vi.stubGlobal('fetch', fetchMock)
    try {
      await apiDownload('/enxovais/id/exportar.csv', 'enxoval.csv')
      expect((fetchMock.mock.calls[0]![1].headers as Headers).get('Authorization')).toMatch(/^Bearer /)
      expect(createObjectURL).toHaveBeenCalledWith(blob)
      expect(click).toHaveBeenCalledOnce()
      vi.runAllTimers()
      expect(revokeObjectURL).toHaveBeenCalledWith('blob:teste')
    } finally {
      click.mockRestore()
      vi.useRealTimers()
    }
  })
})
