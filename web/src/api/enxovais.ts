import { apiFetch } from './cliente'
import type { components } from './tipos'

export type RespostasEntrada = components['schemas']['RespostasEntrada']
export type EnxovalCriado = components['schemas']['EnxovalCriado']

export function criarEnxoval(dados: RespostasEntrada): Promise<EnxovalCriado> {
  return apiFetch<EnxovalCriado>('/enxovais', {
    method: 'POST',
    body: JSON.stringify(dados),
  })
}
