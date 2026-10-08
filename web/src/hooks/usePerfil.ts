import { useQuery } from '@tanstack/react-query'
import { getPerfil } from '../api/perfil'
import { keycloak, keycloakHabilitado } from '../auth/keycloak'

export function usePerfil() {
  return useQuery({
    queryKey: ['perfil', keycloak.subject],
    queryFn: getPerfil,
    enabled: keycloakHabilitado,
    staleTime: 60_000,
  })
}
