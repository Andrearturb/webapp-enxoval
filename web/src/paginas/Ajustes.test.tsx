import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { getEnxoval, apagarEnxoval } from '../api/enxovais'
import { ErroApi } from '../api/cliente'
import type { EnxovalSaida } from '../api/enxovais'
import Ajustes from './Ajustes'

vi.mock('../api/enxovais', async (importOriginal) => {
  const mod = await importOriginal<typeof import('../api/enxovais')>()
  return { ...mod, getEnxoval: vi.fn(), apagarEnxoval: vi.fn() }
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
  alertas: [],
  resumo: { dias_sem_lavar: 2, total_unidades: 0, aviso_volume_alto: false, destacar_ja_tinha: false },
  progresso: { total_unidades: 0, atendidas: 0, faltam: 0, percentual: 0 },
}

function renderAjustes() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/enxoval/id-abc/ajustes']}>
        <Routes>
          <Route path="/enxoval/:id/ajustes" element={<Ajustes />} />
          <Route path="/meus-enxovais" element={<p>MeusEnxovais</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Ajustes', () => {
  it('exibe loading enquanto carrega', () => {
    vi.mocked(getEnxoval).mockReturnValue(new Promise(() => {}))
    renderAjustes()
    expect(screen.getByText(/carregando/i)).toBeInTheDocument()
  })

  it('exibe as respostas atuais do enxoval', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderAjustes()
    await waitFor(() => expect(screen.getByText('Curitiba - PR')).toBeInTheDocument())
    expect(screen.getByText(/apartamento/i)).toBeInTheDocument()
  })

  it('botão apagar dados está presente', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderAjustes()
    await waitFor(() => screen.getByText('Curitiba - PR'))
    expect(screen.getByRole('button', { name: /apagar/i })).toBeInTheDocument()
  })

  it('confirma antes de apagar', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    vi.mocked(apagarEnxoval).mockResolvedValue(undefined)
    renderAjustes()
    await waitFor(() => screen.getByText('Curitiba - PR'))

    fireEvent.click(screen.getByRole('button', { name: /apagar/i }))

    // Deve mostrar confirmação antes de chamar a API
    expect(screen.getByRole('button', { name: /confirmar/i })).toBeInTheDocument()
    expect(apagarEnxoval).not.toHaveBeenCalled()
  })

  it('apaga o enxoval ao confirmar e redireciona', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    vi.mocked(apagarEnxoval).mockResolvedValue(undefined)
    renderAjustes()
    await waitFor(() => screen.getByText('Curitiba - PR'))

    fireEvent.click(screen.getByRole('button', { name: /apagar/i }))
    fireEvent.click(screen.getByRole('button', { name: /confirmar/i }))

    await waitFor(() => expect(apagarEnxoval).toHaveBeenCalledWith('id-abc'))
    await waitFor(() => expect(screen.getByText('MeusEnxovais')).toBeInTheDocument())
  })

  it('mostra erro da API ao falhar ao apagar', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    vi.mocked(apagarEnxoval).mockRejectedValue(
      new ErroApi('erro', 'Falha ao apagar.', 500),
    )
    renderAjustes()
    await waitFor(() => screen.getByText('Curitiba - PR'))

    fireEvent.click(screen.getByRole('button', { name: /apagar/i }))
    fireEvent.click(screen.getByRole('button', { name: /confirmar/i }))

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Falha ao apagar.'))
  })

  // ── Task 6: seção Exportar ────────────────────────────────────────────────

  it('seção Exportar está presente na página', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderAjustes()
    await waitFor(() => screen.getByText('Curitiba - PR'))
    expect(screen.getByText(/exportar/i)).toBeInTheDocument()
  })

  it('link de download XLSX tem href correto', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderAjustes()
    await waitFor(() => screen.getByText('Curitiba - PR'))
    const link = screen.getByRole('link', { name: /xlsx/i })
    expect(link).toHaveAttribute('href', expect.stringContaining('/exportar.xlsx'))
    expect(link).toHaveAttribute('href', expect.stringContaining('id-abc'))
  })

  it('link de download CSV tem href correto', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderAjustes()
    await waitFor(() => screen.getByText('Curitiba - PR'))
    const link = screen.getByRole('link', { name: /csv/i })
    expect(link).toHaveAttribute('href', expect.stringContaining('/exportar.csv'))
    expect(link).toHaveAttribute('href', expect.stringContaining('id-abc'))
  })

  it('link de download PDF tem href correto', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderAjustes()
    await waitFor(() => screen.getByText('Curitiba - PR'))
    const link = screen.getByRole('link', { name: /pdf/i })
    expect(link).toHaveAttribute('href', expect.stringContaining('/exportar.pdf'))
    expect(link).toHaveAttribute('href', expect.stringContaining('id-abc'))
  })

  it('links de exportação têm download attribute', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderAjustes()
    await waitFor(() => screen.getByText('Curitiba - PR'))
    const links = [
      screen.getByRole('link', { name: /xlsx/i }),
      screen.getByRole('link', { name: /csv/i }),
      screen.getByRole('link', { name: /pdf/i }),
    ]
    for (const link of links) {
      expect(link).toHaveAttribute('download')
    }
  })
})
