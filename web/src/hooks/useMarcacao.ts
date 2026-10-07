import { useRef } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { marcarLinha, completarLinha, type EnxovalSaida, type MarcacaoEntrada } from '../api/enxovais'

/**
 * Hook de marcação otimista.
 *
 * `marcar(chave, {comprada, ganhada, ja_tinha})` — atualiza o cache imediatamente
 * e envia o PUT com debounce de 400 ms. Em caso de erro, faz rollback.
 *
 * `completar(chave, origem)` — usa POST /completar; também otimista.
 */
export function useMarcacao(enxovalId: string) {
  const qc = useQueryClient()
  const chaveQuery = ['enxoval', enxovalId] as const

  // Timers de debounce por chave de linha
  const timers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map())

  // Snapshot salvo antes da primeira atualização otimista no debounce
  // (garante rollback para o estado original, não para o intermediário)
  const snapshots = useRef<Map<string, EnxovalSaida>>(new Map())

  const mutacao = useMutation({
    mutationFn: ({ chave, marcacao }: { chave: string; marcacao: MarcacaoEntrada }) =>
      marcarLinha(enxovalId, chave, marcacao),

    onError: (_err, { chave }) => {
      const snapshot = snapshots.current.get(chave)
      if (snapshot) {
        qc.setQueryData(chaveQuery, snapshot)
        snapshots.current.delete(chave)
      }
    },

    onSettled: (_data, _err, { chave }) => {
      snapshots.current.delete(chave)
      qc.invalidateQueries({ queryKey: chaveQuery })
    },
  })

  const mutacaoCompletar = useMutation({
    mutationFn: ({
      chave,
      origem,
    }: {
      chave: string
      origem: 'comprada' | 'ganhada' | 'ja_tinha'
    }) => completarLinha(enxovalId, chave, origem),

    onMutate: async ({ chave, origem }) => {
      await qc.cancelQueries({ queryKey: chaveQuery })
      const snapshot = qc.getQueryData<EnxovalSaida>(chaveQuery)

      qc.setQueryData<EnxovalSaida>(chaveQuery, (atual) => {
        if (!atual) return atual
        return {
          ...atual,
          linhas: atual.linhas.map((l) => {
            if (l.chave !== chave) return l
            return {
              ...l,
              [origem]: l[origem] + l.faltam,
              faltam: 0,
            }
          }),
        }
      })

      return { snapshot }
    },

    onError: (_err, _vars, contexto) => {
      if (contexto?.snapshot) {
        qc.setQueryData(chaveQuery, contexto.snapshot)
      }
    },

    onSettled: () => {
      qc.invalidateQueries({ queryKey: chaveQuery })
    },
  })

  /**
   * Atualiza o cache imediatamente (otimismo) e agenda PUT com debounce de 400 ms.
   * Múltiplas chamadas rápidas para a mesma chave agrupam-se em um único PUT.
   */
  function marcar(chave: string, marcacao: MarcacaoEntrada) {
    // Salva snapshot antes da primeira mudança nesta "rodada" de debounce
    if (!snapshots.current.has(chave)) {
      const atual = qc.getQueryData<EnxovalSaida>(chaveQuery)
      if (atual) snapshots.current.set(chave, atual)
    }

    // Atualiza o cache imediatamente (otimismo)
    qc.setQueryData<EnxovalSaida>(chaveQuery, (atual) => {
      if (!atual) return atual
      const total = marcacao.comprada + marcacao.ganhada + marcacao.ja_tinha
      return {
        ...atual,
        linhas: atual.linhas.map((l) => {
          if (l.chave !== chave) return l
          return {
            ...l,
            comprada: marcacao.comprada,
            ganhada: marcacao.ganhada,
            ja_tinha: marcacao.ja_tinha,
            faltam: Math.max(0, l.quantidade - total),
          }
        }),
      }
    })

    // Cancela debounce anterior para a mesma chave
    const timerAnterior = timers.current.get(chave)
    if (timerAnterior) clearTimeout(timerAnterior)

    const timer = setTimeout(() => {
      timers.current.delete(chave)
      mutacao.mutate({ chave, marcacao })
    }, 400)

    timers.current.set(chave, timer)
  }

  function completar(chave: string, origem: 'comprada' | 'ganhada' | 'ja_tinha') {
    mutacaoCompletar.mutate({ chave, origem })
  }

  return { marcar, completar }
}
