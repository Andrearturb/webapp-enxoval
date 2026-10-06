import { describe, expect, it, vi } from 'vitest'
import { apiFetch } from './cliente'
import { buscarMunicipios } from './municipios'

vi.mock('./cliente', () => ({ apiFetch: vi.fn() }))

describe('buscarMunicipios', () => {
  it('busca com o termo codificado na URL', async () => {
    vi.mocked(apiFetch).mockResolvedValue([])
    await buscarMunicipios('são paulo')
    expect(apiFetch).toHaveBeenCalledWith('/municipios?busca=s%C3%A3o%20paulo')
  })
})
