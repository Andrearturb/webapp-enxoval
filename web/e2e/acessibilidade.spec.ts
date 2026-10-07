/**
 * Testes E2E — Acessibilidade com axe-core.
 *
 * Verifica conformidade WCAG 2.1 nível AA em todas as páginas principais.
 * Violações de impacto "critical" e "serious" causam falha no teste.
 *
 * Nota: validação completa requer testes manuais com leitores de tela reais.
 * Esses testes cobrem o que é automatizável (contraste, rótulos, estrutura).
 */
import { test } from '@playwright/test'
import { checkA11y, injectAxe } from 'axe-playwright'
import { criarEnxoval, irParaPlanilha } from './fixtures'

/** Opções axe: reportar apenas violações críticas e sérias. */
const AXE_OPTIONS = {
  runOnly: {
    type: 'tag' as const,
    values: ['wcag2a', 'wcag2aa', 'wcag21aa'],
  },
  resultTypes: ['violations' as const],
}

const VIOLACOES_CRITICAS = {
  includedImpacts: ['critical', 'serious'] as const,
}

test.describe('Acessibilidade — páginas públicas', () => {
  test('Página inicial não tem violações críticas', async ({ page }) => {
    await page.goto('/')
    await injectAxe(page)
    await checkA11y(page, undefined, {
      axeOptions: AXE_OPTIONS,
      violationCounts: VIOLACOES_CRITICAS,
    })
  })

  test('Passo 1 do questionário (cidade) não tem violações críticas', async ({ page }) => {
    await page.goto('/questionario/1')
    await page.waitForSelector('label[for="cidade"]')
    await injectAxe(page)
    await checkA11y(page, undefined, {
      axeOptions: AXE_OPTIONS,
      violationCounts: VIOLACOES_CRITICAS,
    })
  })
})

test.describe('Acessibilidade — páginas do enxoval', () => {
  // Cada teste cria seu próprio enxoval para evitar estado compartilhado
  test('Planilha não tem violações críticas', async ({ page }) => {
    const id = await criarEnxoval()
    await irParaPlanilha(page, id)
    await injectAxe(page)
    await checkA11y(page, undefined, {
      axeOptions: AXE_OPTIONS,
      violationCounts: VIOLACOES_CRITICAS,
    })
  })

  test('Roteiro não tem violações críticas', async ({ page }) => {
    const id = await criarEnxoval()
    await page.goto(`/enxoval/${id}/roteiro`)
    await page.waitForSelector('main')
    await injectAxe(page)
    await checkA11y(page, undefined, {
      axeOptions: AXE_OPTIONS,
      violationCounts: VIOLACOES_CRITICAS,
    })
  })

  test('Guia não tem violações críticas', async ({ page }) => {
    const id = await criarEnxoval()
    await page.goto(`/enxoval/${id}/guia`)
    await page.waitForSelector('main')
    await injectAxe(page)
    await checkA11y(page, undefined, {
      axeOptions: AXE_OPTIONS,
      violationCounts: VIOLACOES_CRITICAS,
    })
  })

  test('Segurança não tem violações críticas', async ({ page }) => {
    const id = await criarEnxoval()
    await page.goto(`/enxoval/${id}/seguranca`)
    await page.waitForSelector('main')
    await injectAxe(page)
    await checkA11y(page, undefined, {
      axeOptions: AXE_OPTIONS,
      violationCounts: VIOLACOES_CRITICAS,
    })
  })

  test('Ajustes não tem violações críticas', async ({ page }) => {
    const id = await criarEnxoval()
    await page.goto(`/enxoval/${id}/ajustes`)
    await page.waitForSelector('text=Curitiba')
    await injectAxe(page)
    await checkA11y(page, undefined, {
      axeOptions: AXE_OPTIONS,
      violationCounts: VIOLACOES_CRITICAS,
    })
  })
})
