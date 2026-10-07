import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { getEnxoval } from '../api/enxovais'
import { ErroApi } from '../api/cliente'
import type { EnxovalSaida } from '../api/enxovais'
import Roteiro from './Roteiro'

vi.mock('../api/enxovais', async (importOriginal) => {
  const mod = await importOriginal<typeof import('../api/enxovais')>()
  return { ...mod, getEnxoval: vi.fn() }
})

const enxovalFixture: EnxovalSaida = {
  id: 'id-abc',
  respostas: {
    municipio: { codigo_ibge: 4106902, nome: 'Curitiba', uf: 'PR' },
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
  linhas: [],
  linhas_fora_da_lista: [],
  fichas: [],
  roteiro: [
    {
      codigo: 'reta-final',
      nome: 'Reta final',
      texto: 'Monte a mala maternidade e providencie o berço.',
      inicio: '2027-03-15',
      fim: '2027-06-15',
      atual: false,
    },
    {
      codigo: 'primeiro-mes',
      nome: 'Primeiro mês',
      texto: 'Cuide dos documentos e das vacinas.',
      inicio: '2027-06-15',
      fim: '2027-07-15',
      atual: true,
    },
  ],
  alertas: [],
  resumo: { dias_sem_lavar: 2, total_unidades: 0, aviso_volume_alto: false, destacar_ja_tinha: false },
  progresso: { total_unidades: 0, atendidas: 0, faltam: 0, percentual: 0 },
}

function renderRoteiro() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/enxoval/id-abc/roteiro']}>
        <Routes>
          <Route path="/enxoval/:id/roteiro" element={<Roteiro />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Roteiro', () => {
  it('exibe loading enquanto carrega', () => {
    vi.mocked(getEnxoval).mockReturnValue(new Promise(() => {}))
    renderRoteiro()
    expect(screen.getByText(/carregando/i)).toBeInTheDocument()
  })

  it('exibe erro quando o enxoval não é encontrado', async () => {
    vi.mocked(getEnxoval).mockRejectedValue(new ErroApi('nao_encontrado', 'Enxoval não encontrado.', 404))
    renderRoteiro()
    await waitFor(() => expect(screen.getByText(/não encontrado/i)).toBeInTheDocument())
  })

  it('lista as fases do roteiro', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderRoteiro()
    await waitFor(() => expect(screen.getByText('Reta final')).toBeInTheDocument())
    expect(screen.getByText('Primeiro mês')).toBeInTheDocument()
  })

  it('destaca a fase atual visualmente', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderRoteiro()
    await waitFor(() => screen.getByText('Primeiro mês'))
    const faseAtual = screen.getByText('Primeiro mês').closest('[data-testid="fase"]')
    expect(faseAtual).toHaveAttribute('data-atual', 'true')
  })

  it('mostra o texto e as datas de cada fase', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderRoteiro()
    await waitFor(() => screen.getByText('Reta final'))
    expect(screen.getByText(/monte a mala maternidade/i)).toBeInTheDocument()
  })
})
