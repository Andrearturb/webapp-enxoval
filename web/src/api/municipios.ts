import { apiFetch } from './cliente'
import type { components } from './tipos'

export type Municipio = components['schemas']['MunicipioBuscaSaida']

export function buscarMunicipios(busca: string): Promise<Municipio[]> {
  return apiFetch<Municipio[]>(`/municipios?busca=${encodeURIComponent(busca)}`)
}
