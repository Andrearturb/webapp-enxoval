import { apiFetch } from './cliente'
import type { components } from './tipos'

export type RespostasEntrada = components['schemas']['RespostasEntrada']
export type EnxovalCriado = components['schemas']['EnxovalCriado']
export type EnxovalSaida = components['schemas']['EnxovalSaida']
export type LinhaSaida = components['schemas']['LinhaSaida']
export type CategoriaSaida = components['schemas']['CategoriaSaida']
export type MarcacaoEntrada = components['schemas']['MarcacaoEntrada']
export type Prioridade = components['schemas']['Prioridade']
export type Tamanho = components['schemas']['Tamanho']

export function criarEnxoval(dados: RespostasEntrada): Promise<EnxovalCriado> {
  return apiFetch<EnxovalCriado>('/enxovais', {
    method: 'POST',
    body: JSON.stringify(dados),
  })
}

export function getEnxoval(id: string): Promise<EnxovalSaida> {
  return apiFetch<EnxovalSaida>(`/enxovais/${id}`)
}

export function marcarLinha(
  id: string,
  chave: string,
  marcacao: MarcacaoEntrada,
): Promise<EnxovalSaida> {
  return apiFetch<EnxovalSaida>(`/enxovais/${id}/linhas/${encodeURIComponent(chave)}`, {
    method: 'PUT',
    body: JSON.stringify(marcacao),
  })
}

export function completarLinha(
  id: string,
  chave: string,
  origem: 'comprada' | 'ganhada' | 'ja_tinha',
): Promise<EnxovalSaida> {
  return apiFetch<EnxovalSaida>(
    `/enxovais/${id}/linhas/${encodeURIComponent(chave)}/completar`,
    {
      method: 'POST',
      body: JSON.stringify({ origem }),
    },
  )
}

export function editarEnxoval(id: string, dados: RespostasEntrada): Promise<EnxovalSaida> {
  return apiFetch<EnxovalSaida>(`/enxovais/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(dados),
  })
}

export function apagarEnxoval(id: string): Promise<void> {
  return apiFetch<void>(`/enxovais/${id}`, { method: 'DELETE' })
}
