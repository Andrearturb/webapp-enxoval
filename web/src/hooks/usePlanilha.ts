import { useQuery } from '@tanstack/react-query'
import { getEnxoval } from '../api/enxovais'
import { ErroApi } from '../api/cliente'

export function usePlanilha(id: string) {
  return useQuery({
    queryKey: ['enxoval', id],
    queryFn: () => getEnxoval(id),
    staleTime: 60_000, // 60 s — planilha não precisa re-fetch a cada foco
    retry: (tentativas, erro) => {
      // Não tentar novamente em 404
      if (erro instanceof ErroApi && erro.status === 404) return false
      return tentativas < 2
    },
  })
}
