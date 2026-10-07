import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { FaseSaida, LinhaSaida } from '../../api/enxovais'
import { PainelFases } from './PainelFases'

// ── fixtures ──────────────────────────────────────────────────────────────────

const fases: FaseSaida[] = [
  {
    codigo: 'gestacao_inicio',
    nome: 'Início da gestação',
    texto: '',
    inicio: '2026-01-01',
    fim: '2026-04-30',
    atual: false,
  },
  {
    codigo: 'reta_final',
    nome: 'Reta final',
    texto: '',
    inicio: '2026-05-01',
    fim: '2026-08-31',
    atual: true,
  },
  {
    codigo: 'primeiros_meses',
    nome: 'Primeiros meses',
    texto: '',
    inicio: '2026-09-01',
    fim: '2026-12-31',
    atual: false,
  },
]

function linhaBase(override: Partial<LinhaSaida> = {}): LinhaSaida {
  return {
    chave: 'body::',
    item_slug: 'body',
    nome: 'Body',
    rotulo_variante: null,
    categoria_slug: 'roupas',
    tamanho: null,
    quantidade: 1,
    unidade_texto: null,
    prioridade: 'essencial',
    fase_codigo: 'reta_final',
    momento_compra: 'agora',
    e_seguranca: false,
    comprada: 0,
    ganhada: 0,
    ja_tinha: 0,
    faltam: 1,
    ...override,
  }
}

const linhas: LinhaSaida[] = [
  linhaBase({ chave: 'body::', fase_codigo: 'reta_final' }),
  linhaBase({ chave: 'fralda::', nome: 'Fralda', fase_codigo: 'reta_final' }),
  linhaBase({ chave: 'berco::', nome: 'Berço', fase_codigo: 'primeiros_meses' }),
  // gestacao_inicio não tem linhas — card não deve aparecer
]

// ── testes ────────────────────────────────────────────────────────────────────

describe('PainelFases', () => {
  it('mostra cards apenas para fases que têm itens', () => {
    const onFaseFiltrada = vi.fn()
    render(
      <PainelFases
        fases={fases}
        linhas={linhas}
        faseFiltrada={null}
        onFaseFiltrada={onFaseFiltrada}
      />,
    )

    // "Reta final" e "Primeiros meses" têm itens → cards visíveis
    expect(screen.getByRole('button', { name: /reta final/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /primeiros meses/i })).toBeInTheDocument()
    // "Início da gestação" não tem itens → card ausente
    expect(screen.queryByRole('button', { name: /início da gestação/i })).not.toBeInTheDocument()
  })

  it('mostra a contagem de itens em cada card', () => {
    render(
      <PainelFases
        fases={fases}
        linhas={linhas}
        faseFiltrada={null}
        onFaseFiltrada={vi.fn()}
      />,
    )

    // "Reta final" tem 2 itens
    expect(screen.getByRole('button', { name: /reta final/i })).toHaveTextContent('2')
    // "Primeiros meses" tem 1 item
    expect(screen.getByRole('button', { name: /primeiros meses/i })).toHaveTextContent('1')
  })

  it('clicar em uma fase chama onFaseFiltrada com o código da fase', () => {
    const onFaseFiltrada = vi.fn()
    render(
      <PainelFases
        fases={fases}
        linhas={linhas}
        faseFiltrada={null}
        onFaseFiltrada={onFaseFiltrada}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /primeiros meses/i }))

    expect(onFaseFiltrada).toHaveBeenCalledWith('primeiros_meses')
  })

  it('fase atual está destacada visualmente', () => {
    render(
      <PainelFases
        fases={fases}
        linhas={linhas}
        faseFiltrada={null}
        onFaseFiltrada={vi.fn()}
      />,
    )

    const cardAtual = screen.getByRole('button', { name: /reta final/i })
    expect(cardAtual.className).toMatch(/bg-principal/)
  })

  it('fase passada com itens não comprados mostra badge de alerta', () => {
    const linhasComAtrasado: LinhaSaida[] = [
      linhaBase({ chave: 'body::', fase_codigo: 'gestacao_inicio', faltam: 1 }),
      linhaBase({ chave: 'fralda::', nome: 'Fralda', fase_codigo: 'reta_final', faltam: 0, comprada: 1 }),
    ]
    render(
      <PainelFases
        fases={fases}
        linhas={linhasComAtrasado}
        faseFiltrada={null}
        onFaseFiltrada={vi.fn()}
      />,
    )

    // "Início da gestação" é fase passada com item não comprado
    const cardPassado = screen.getByRole('button', { name: /início da gestação/i })
    // Deve ter um badge de alerta dentro do card
    expect(cardPassado.querySelector('[data-testid="badge-alerta"]')).not.toBeNull()
  })

  it('clicar no card já ativo limpa o filtro (toggle)', () => {
    const onFaseFiltrada = vi.fn()
    render(
      <PainelFases
        fases={fases}
        linhas={linhas}
        faseFiltrada="reta_final"
        onFaseFiltrada={onFaseFiltrada}
      />,
    )

    // Clica no card que já está ativo
    fireEvent.click(screen.getByRole('button', { name: /reta final/i }))

    // Deve chamar com null para limpar o filtro
    expect(onFaseFiltrada).toHaveBeenCalledWith(null)
  })
})
