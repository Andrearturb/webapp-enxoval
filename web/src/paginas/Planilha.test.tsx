import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter as MemRouter, Route as Rt, Routes as Rts } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { getEnxoval, marcarLinha } from '../api/enxovais'
import { ErroApi } from '../api/cliente'
import type { EnxovalSaida } from '../api/enxovais'
import Planilha from './Planilha'

vi.mock('../api/enxovais', async (importOriginal) => {
  const mod = await importOriginal<typeof import('../api/enxovais')>()
  return { ...mod, getEnxoval: vi.fn(), marcarLinha: vi.fn() }
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
  categorias: [
    { slug: 'roupas', nome: 'Roupas', ordem: 1 },
    { slug: 'higiene', nome: 'Higiene', ordem: 2 },
  ],
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
    {
      chave: 'fralda::',
      item_slug: 'fralda',
      nome: 'Fralda descartável',
      rotulo_variante: null,
      categoria_slug: 'higiene',
      tamanho: null,
      quantidade: 4,
      unidade_texto: 'pacotes',
      prioridade: 'essencial',
      fase_codigo: 'pre-natal',
      momento_compra: 'agora',
      e_seguranca: false,
      comprada: 2,
      ganhada: 0,
      ja_tinha: 0,
      faltam: 2,
    },
  ],
  linhas_fora_da_lista: [],
  fichas: [],
  roteiro: [],
  alertas: [],
  resumo: { dias_sem_lavar: 2, total_unidades: 10, aviso_volume_alto: false, destacar_ja_tinha: false },
  progresso: { total_unidades: 10, atendidas: 2, faltam: 8, percentual: 20 },
}

function renderPlanilha(id = 'id-abc') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={qc}>
      <MemRouter initialEntries={[`/enxoval/${id}/planilha`]}>
        <Rts>
          <Rt path="/enxoval/:id/planilha" element={<Planilha />} />
        </Rts>
      </MemRouter>
    </QueryClientProvider>,
  )
  return { qc }
}

describe('Planilha', () => {
  it('exibe loading enquanto carrega', () => {
    vi.mocked(getEnxoval).mockReturnValue(new Promise(() => {}))
    renderPlanilha()
    expect(screen.getByText(/carregando/i)).toBeInTheDocument()
  })

  it('exibe mensagem de erro 404 quando enxoval não é encontrado', async () => {
    vi.mocked(getEnxoval).mockRejectedValue(new ErroApi('nao_encontrado', 'Enxoval não encontrado.', 404))
    renderPlanilha()
    await waitFor(() => expect(screen.getByText(/não encontrado/i)).toBeInTheDocument())
  })

  it('exibe as categorias e linhas após carregar', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderPlanilha()
    await waitFor(() => expect(screen.getByText('Roupas')).toBeInTheDocument())
    expect(screen.getByText('Higiene')).toBeInTheDocument()
    // "Body P" — nome + tamanho estão no mesmo span
    expect(screen.getByText(/^Body/)).toBeInTheDocument()
    expect(screen.getByText('Fralda descartável')).toBeInTheDocument()
  })

  it('exibe a barra de progresso com os valores corretos', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    renderPlanilha()
    await waitFor(() => expect(screen.getByText('20%')).toBeInTheDocument())
    expect(screen.getByText(/2 de 10/)).toBeInTheDocument()
  })

  it('filtro "Faltando" oculta linhas completamente atendidas', async () => {
    const enxovalCompleto = {
      ...enxovalFixture,
      linhas: [
        { ...enxovalFixture.linhas[0], comprada: 6, faltam: 0 },
        enxovalFixture.linhas[1],
      ],
    }
    vi.mocked(getEnxoval).mockResolvedValue(enxovalCompleto)
    renderPlanilha()
    await waitFor(() => screen.getByText('Roupas'))

    fireEvent.click(screen.getByRole('button', { name: /faltando/i }))

    expect(screen.queryByText(/^Body/)).not.toBeInTheDocument()
    expect(screen.getByText('Fralda descartável')).toBeInTheDocument()
  })

  it('incrementar comprada atualiza o contador visualmente', async () => {
    vi.mocked(getEnxoval).mockResolvedValue(enxovalFixture)
    vi.mocked(marcarLinha).mockResolvedValue({
      ...enxovalFixture,
      linhas: [
        { ...enxovalFixture.linhas[0], comprada: 1, faltam: 5 },
        enxovalFixture.linhas[1],
      ],
    })
    renderPlanilha()
    await waitFor(() => screen.getByText('Roupas'))

    // Expande a linha do Body clicando nela
    const linhaBody = screen.getByText(/^Body/).closest('[data-testid="linha-item"]')
    expect(linhaBody).not.toBeNull()
    fireEvent.click(linhaBody!.querySelector('button')!)

    // Agora os contadores aparecem — clica em + Comprada
    await waitFor(() => screen.getByRole('button', { name: /\+ comprada/i }))
    const botaoMais = screen.getByRole('button', { name: /\+ comprada/i })
    fireEvent.click(botaoMais)

    // O valor deve atualizar otimisticamente
    await waitFor(() => {
      const linhaAtualizada = screen.getByText(/^Body/).closest('[data-testid="linha-item"]') as HTMLElement
      expect(within(linhaAtualizada).getByText('1')).toBeInTheDocument()
    })
  })

  // ── Task 5: agrupamento por momento_compra ─────────────────────────────────

  it('agrupa itens atrasados antes dos itens da fase atual', async () => {
    const enxovalComAtrasado: EnxovalSaida = {
      ...enxovalFixture,
      linhas: [
        {
          ...enxovalFixture.linhas[0],
          chave: 'body:RN:',
          nome: 'Body RN',
          tamanho: null,
          momento_compra: 'atrasado',
        },
        {
          ...enxovalFixture.linhas[1],
          nome: 'Fralda descartável',
          momento_compra: 'agora',
        },
      ],
    }
    vi.mocked(getEnxoval).mockResolvedValue(enxovalComAtrasado)
    renderPlanilha()

    // Ambos os grupos devem aparecer na tela
    await waitFor(() => screen.getByText(/comprar agora/i))
    await waitFor(() => screen.getByText(/nesta fase/i))

    // O grupo "Comprar agora" deve aparecer antes do grupo "Nesta fase" no DOM
    const grupoAtrasado = screen.getByText(/comprar agora/i).closest('[data-momento="atrasado"]')
    const grupoAgora = screen.getByText(/nesta fase/i).closest('[data-momento="agora"]')
    expect(grupoAtrasado).not.toBeNull()
    expect(grupoAgora).not.toBeNull()

    // "atrasado" deve preceder "agora" no DOM
    expect(
      grupoAtrasado!.compareDocumentPosition(grupoAgora!) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()
  })

  it('grupo "Mais para frente" começa colapsado', async () => {
    const enxovalComFuturo: EnxovalSaida = {
      ...enxovalFixture,
      linhas: [
        {
          ...enxovalFixture.linhas[0],
          nome: 'Berço',
          momento_compra: 'futuro',
        },
      ],
    }
    vi.mocked(getEnxoval).mockResolvedValue(enxovalComFuturo)
    renderPlanilha()

    await waitFor(() => screen.getByText(/mais para frente/i))

    // O item dentro do grupo "futuro" não deve estar visível (grupo colapsado)
    expect(screen.queryByText('Berço')).not.toBeInTheDocument()
  })

  it('filtro Essencial funciona dentro de cada grupo', async () => {
    const enxovalMisto: EnxovalSaida = {
      ...enxovalFixture,
      linhas: [
        {
          ...enxovalFixture.linhas[0],
          chave: 'body::',
          nome: 'Body essencial',
          tamanho: null,
          prioridade: 'essencial',
          momento_compra: 'agora',
        },
        {
          ...enxovalFixture.linhas[1],
          chave: 'chupeta::',
          nome: 'Chupeta',
          prioridade: 'pode_esperar',
          momento_compra: 'agora',
        },
      ],
    }
    vi.mocked(getEnxoval).mockResolvedValue(enxovalMisto)
    renderPlanilha()

    await waitFor(() => screen.getByText('Body essencial'))
    expect(screen.getByText('Chupeta')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Essencial' }))

    expect(screen.getByText('Body essencial')).toBeInTheDocument()
    expect(screen.queryByText('Chupeta')).not.toBeInTheDocument()
  })

  it('item com momento_compra=atrasado tem destaque visual diferente dos demais', async () => {    const enxovalComAtrasado: EnxovalSaida = {
      ...enxovalFixture,
      linhas: [
        {
          ...enxovalFixture.linhas[0],
          nome: 'Body atrasado',
          tamanho: null,
          momento_compra: 'atrasado',
        },
        {
          ...enxovalFixture.linhas[1],
          nome: 'Fralda normal',
          momento_compra: 'agora',
        },
      ],
    }
    vi.mocked(getEnxoval).mockResolvedValue(enxovalComAtrasado)
    renderPlanilha()

    await waitFor(() => screen.getByText(/comprar agora/i))

    // O grupo atrasado deve ter atributo data-momento="atrasado" e classe de alerta
    const secaoAtrasada = screen.getByText(/comprar agora/i).closest('[data-momento="atrasado"]')
    expect(secaoAtrasada).not.toBeNull()
    expect(secaoAtrasada!.className).toMatch(/alerta/)
  })

  // ── Task 6: integração PainelFases na Planilha ────────────────────────────

  it('exibe painel de fases quando roteiro não está vazio', async () => {
    const enxovalComRoteiro: EnxovalSaida = {
      ...enxovalFixture,
      roteiro: [
        {
          codigo: 'pre-natal',
          nome: 'Pré-natal',
          texto: '',
          inicio: '2026-01-01',
          fim: '2026-06-01',
          atual: true,
        },
      ],
    }
    vi.mocked(getEnxoval).mockResolvedValue(enxovalComRoteiro)
    renderPlanilha()

    await waitFor(() => screen.getByRole('button', { name: /pré-natal/i }))
    expect(screen.getByRole('button', { name: /pré-natal/i })).toBeInTheDocument()
  })

  it('clicar em fase no painel filtra os grupos exibidos', async () => {
    const enxovalComRoteiro: EnxovalSaida = {
      ...enxovalFixture,
      roteiro: [
        {
          codigo: 'pre-natal',
          nome: 'Pré-natal',
          texto: '',
          inicio: '2026-01-01',
          fim: '2026-06-01',
          atual: true,
        },
        {
          codigo: 'primeiros-meses',
          nome: 'Primeiros meses',
          texto: '',
          inicio: '2026-06-02',
          fim: '2026-12-31',
          atual: false,
        },
      ],
      linhas: [
        {
          ...enxovalFixture.linhas[0],
          fase_codigo: 'pre-natal',
          momento_compra: 'agora',
        },
        {
          ...enxovalFixture.linhas[1],
          fase_codigo: 'primeiros-meses',
          momento_compra: 'proxima_fase',
        },
      ],
    }
    vi.mocked(getEnxoval).mockResolvedValue(enxovalComRoteiro)
    renderPlanilha()

    await waitFor(() => screen.getByRole('button', { name: /primeiros meses/i }))

    // Clica no card "Primeiros meses" — deve filtrar para só essa fase
    fireEvent.click(screen.getByRole('button', { name: /primeiros meses/i }))

    // "Fralda descartável" (primeiros-meses) deve aparecer; "Body" (pre-natal) não
    await waitFor(() => expect(screen.getByText('Fralda descartável')).toBeInTheDocument())
    expect(screen.queryByText(/^Body/)).not.toBeInTheDocument()
  })
})
