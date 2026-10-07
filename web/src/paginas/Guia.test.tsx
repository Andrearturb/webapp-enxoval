import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { getEnxoval } from '../api/enxovais'
import type { EnxovalSaida } from '../api/enxovais'
import Guia from './Guia'
import GuiaItem from './GuiaItem'

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
  fichas: [
    {
      slug: 'body',
      nome: 'Body',
      para_que_serve: 'Roupa básica do bebê.',
      como_escolher: 'Prefira 100% algodão.',
      idade_inicio_meses: 0,
      marcas: { nomes: ['Tip Top', 'Carter\'s'], faixa: 'intermediario', faixa_aproximada: false },
      dicas: ['Compre em tamanhos variados.'],
      regras_seguranca: [],
    },
    {
      slug: 'berco',
      nome: 'Berço',
      para_que_serve: 'Local seguro para o bebê dormir.',
      como_escolher: 'Verifique o selo do INMETRO.',
      idade_inicio_meses: 0,
      marcas: { nomes: ['Galzerano'], faixa: 'intermediario', faixa_aproximada: false },
      dicas: ['O colchão deve ser firme.'],
      regras_seguranca: ['Sem travesseiro até 2 anos.'],
    },
  ],
  roteiro: [],
  alertas: [],
  resumo: { dias_sem_lavar: 2, total_unidades: 0, aviso_volume_alto: false, destacar_ja_tinha: false },
  progresso: { total_unidades: 0, atendidas: 0, faltam: 0, percentual: 0 },
}

function renderGuia(caminho = '/enxoval/id-abc/guia') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[caminho]}>
        <Routes>
          <Route path="/enxoval/:id/guia" element={<Guia />} />
          <Route path="/enxoval/:id/guia/:item" element={<GuiaItem />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Guia (lista)', () => {
  it('lista as fichas de itens', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderGuia()
    await waitFor(() => expect(screen.getByText('Body')).toBeInTheDocument())
    expect(screen.getByText('Berço')).toBeInTheDocument()
  })

  it('navega para a ficha do item ao clicar', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderGuia()
    await waitFor(() => screen.getByText('Body'))
    fireEvent.click(screen.getByText('Body'))
    // Deve renderizar a ficha do body
    await waitFor(() => expect(screen.getByText('Roupa básica do bebê.')).toBeInTheDocument())
  })
})

describe('GuiaItem (ficha individual)', () => {
  it('exibe os detalhes da ficha do item', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderGuia('/enxoval/id-abc/guia/berco')
    await waitFor(() => expect(screen.getByText('Berço')).toBeInTheDocument())
    expect(screen.getByText('Local seguro para o bebê dormir.')).toBeInTheDocument()
    expect(screen.getByText('Verifique o selo do INMETRO.')).toBeInTheDocument()
    expect(screen.getByText('Galzerano')).toBeInTheDocument()
  })

  it('exibe regras de segurança quando existem', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderGuia('/enxoval/id-abc/guia/berco')
    await waitFor(() => screen.getByText('Berço'))
    expect(screen.getByText('Sem travesseiro até 2 anos.')).toBeInTheDocument()
  })

  it('mostra 404 quando o slug não existe nas fichas', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderGuia('/enxoval/id-abc/guia/nao-existe')
    await waitFor(() => expect(screen.getByText(/não encontrado/i)).toBeInTheDocument())
  })
})
