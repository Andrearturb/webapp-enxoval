import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { marcarLinha } from '../api/enxovais'
import { useMarcacao } from './useMarcacao'
import type { EnxovalSaida } from '../api/enxovais'

vi.mock('../api/enxovais', async (importOriginal) => {
  const mod = await importOriginal<typeof import('../api/enxovais')>()
  return { ...mod, marcarLinha: vi.fn() }
})

const enxovalBase: EnxovalSaida = {
  id: 'id-teste',
  respostas: {
    municipio: { codigo_ibge: 1, nome: 'Curitiba', uf: 'PR' },
    perfil_clima: 'frio',
    perfil_corrigido: false,
    data_prevista: '2027-06-15',
    dias_entre_lavagens: 2,
    moradia: 'apartamento',
    tem_carro: false,
    orcamento: 'intermediario',
    primeiro_filho: true,
  },
  categorias: [],
  linhas: [
    {
      chave: 'body:P:',
      item_slug: 'body',
      nome: 'Body',
      rotulo_variante: null,
      categoria_slug: 'roupas',
      tamanho: 'P',
      quantidade: 6,
      unidade_texto: null,
      prioridade: 'essencial',
      fase_codigo: 'pre-natal',
      momento_compra: 'agora',
      e_seguranca: false,
      comprada: 0,
      ganhada: 0,
      ja_tinha: 0,
      faltam: 6,
    },
  ],
  linhas_fora_da_lista: [],
  fichas: [],
  roteiro: [],
  alertas: [],
  resumo: { dias_sem_lavar: 2, total_unidades: 6, aviso_volume_alto: false, destacar_ja_tinha: false },
  progresso: { total_unidades: 6, atendidas: 0, faltam: 6, percentual: 0 },
}

function criarWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  qc.setQueryData(['enxoval', 'id-teste'], enxovalBase)
  return {
    qc,
    wrapper: ({ children }: { children: React.ReactNode }) =>
      createElement(QueryClientProvider, { client: qc }, children),
  }
}

describe('useMarcacao', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('atualiza otimisticamente o cache ao marcar', async () => {
    vi.mocked(marcarLinha).mockResolvedValue({
      ...enxovalBase,
      linhas: [{ ...enxovalBase.linhas[0], comprada: 1, faltam: 5 }],
    })

    const { qc, wrapper } = criarWrapper()
    const { result } = renderHook(() => useMarcacao('id-teste'), { wrapper })

    act(() => {
      result.current.marcar('body:P:', { comprada: 1, ganhada: 0, ja_tinha: 0 })
    })

    // Atualização otimista deve ser imediata (síncrona)
    const cache = qc.getQueryData<EnxovalSaida>(['enxoval', 'id-teste'])
    expect(cache?.linhas[0].comprada).toBe(1)
    expect(cache?.linhas[0].faltam).toBe(5)
  })

  it('faz rollback no cache quando a mutação falha', async () => {
    vi.mocked(marcarLinha).mockRejectedValue(new Error('falha de rede'))

    const { qc, wrapper } = criarWrapper()
    const { result } = renderHook(() => useMarcacao('id-teste'), { wrapper })

    act(() => {
      result.current.marcar('body:P:', { comprada: 1, ganhada: 0, ja_tinha: 0 })
    })

    await waitFor(() => {
      const cache = qc.getQueryData<EnxovalSaida>(['enxoval', 'id-teste'])
      expect(cache?.linhas[0].comprada).toBe(0)
    })
  })
})
