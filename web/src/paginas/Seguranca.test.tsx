import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { getEnxoval } from '../api/enxovais'
import type { EnxovalSaida } from '../api/enxovais'
import Seguranca from './Seguranca'

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
  roteiro: [],
  alertas: [
    {
      codigo: 'sono-seguro',
      tema: 'sono',
      texto: 'Bebê deve dormir de costas em superfície firme.',
      base: 'SBP',
      ativo_a_partir: '2027-06-15',
      ativo_ate: '2028-06-15',
      itens: ['berco', 'monitor-bebe'],
    },
    {
      codigo: 'cadeirinha',
      tema: 'transporte',
      texto: 'Use cadeirinha aprovada pelo INMETRO em todos os deslocamentos.',
      base: 'CONTRAN',
      ativo_a_partir: '2027-06-15',
      ativo_ate: '2030-06-15',
      itens: ['bebe-conforto'],
    },
  ],
  resumo: { dias_sem_lavar: 2, total_unidades: 0, aviso_volume_alto: false, destacar_ja_tinha: false },
  progresso: { total_unidades: 0, atendidas: 0, faltam: 0, percentual: 0 },
}

function renderSeguranca() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/enxoval/id-abc/seguranca']}>
        <Routes>
          <Route path="/enxoval/:id/seguranca" element={<Seguranca />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Segurança', () => {
  it('exibe loading enquanto carrega', () => {
    vi.mocked(getEnxoval).mockReturnValue(new Promise(() => {}))
    renderSeguranca()
    expect(screen.getByText(/carregando/i)).toBeInTheDocument()
  })

  it('lista os alertas de segurança', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderSeguranca()
    await waitFor(() =>
      expect(screen.getByText('Bebê deve dormir de costas em superfície firme.')).toBeInTheDocument(),
    )
    expect(
      screen.getByText('Use cadeirinha aprovada pelo INMETRO em todos os deslocamentos.'),
    ).toBeInTheDocument()
  })

  it('filtra alertas por tema', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderSeguranca()
    await waitFor(() => screen.getByText('Bebê deve dormir de costas em superfície firme.'))

    fireEvent.click(screen.getByRole('button', { name: /transporte/i }))

    expect(
      screen.queryByText('Bebê deve dormir de costas em superfície firme.'),
    ).not.toBeInTheDocument()
    expect(
      screen.getByText('Use cadeirinha aprovada pelo INMETRO em todos os deslocamentos.'),
    ).toBeInTheDocument()
  })

  it('mostra a fonte (base) de cada alerta', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderSeguranca()
    await waitFor(() => screen.getByText('SBP'))
    expect(screen.getByText('CONTRAN')).toBeInTheDocument()
  })
})
