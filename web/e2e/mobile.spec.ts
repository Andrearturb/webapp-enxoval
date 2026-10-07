/**
 * Testes E2E — Mobile (viewport Pixel 7 / ~412×915).
 *
 * Repete o fluxo principal em tela pequena para garantir que a UI
 * mobile-first funciona corretamente em dispositivos reais.
 *
 * O projeto `mobile-chrome` no playwright.config.ts já usa o viewport
 * do Pixel 7 — esses testes herdam esse comportamento automaticamente
 * quando rodados no projeto `mobile-chrome`.
 */
import { test, expect } from '@playwright/test'
import { criarEnxoval, irParaPlanilha } from './fixtures'

test.describe('Mobile — Planilha', () => {
  test('planilha renderiza e exibe itens em viewport mobile', async ({ page }) => {
    const id = await criarEnxoval()
    await irParaPlanilha(page, id)

    // Grupos de momento_compra devem aparecer
    await expect(page.locator('[data-momento]').first()).toBeVisible()

    // Pelo menos um item deve ser visível
    await expect(page.getByTestId('linha-item').first()).toBeVisible()
  })

  test('abas de navegação são acessíveis em mobile', async ({ page }) => {
    const id = await criarEnxoval()
    await irParaPlanilha(page, id)

    // As abas devem ser visíveis e clicáveis em tela pequena
    const abaRoteiro = page.getByRole('link', { name: 'Roteiro' })
    await expect(abaRoteiro).toBeVisible()
    await abaRoteiro.click()
    await expect(page).toHaveURL(/\/roteiro/)  })

  test('filtros da planilha funcionam em mobile', async ({ page }) => {
    const id = await criarEnxoval()
    await irParaPlanilha(page, id)

    const btnEssencial = page.getByRole('group', { name: /filtros da planilha/i })
      .getByRole('button', { name: 'Essencial' })
    await expect(btnEssencial).toBeVisible()
    await btnEssencial.click()

    // Verifica que o filtro foi ativado (aria-pressed=true)
    await expect(btnEssencial).toHaveAttribute('aria-pressed', 'true')
  })

  test('expandir linha funciona em mobile (alvos de toque ≥ 44px)', async ({ page }) => {
    const id = await criarEnxoval()
    await irParaPlanilha(page, id)

    const primeiroItem = page.getByTestId('linha-item').first()
    const botao = primeiroItem.getByRole('button').first()

    // Verifica tamanho mínimo do alvo de toque
    const bbox = await botao.boundingBox()
    expect(bbox).not.toBeNull()
    expect(bbox!.height).toBeGreaterThanOrEqual(44)

    await botao.click()
    await expect(page.getByRole('button', { name: /\+ comprada/i })).toBeVisible()
  })
})

test.describe('Mobile — Questionário', () => {
  test('página inicial exibe botão de início em mobile', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('link', { name: /começar meu enxoval/i }).first()).toBeVisible()
  })

  test('passo 1 do questionário funciona em mobile', async ({ page }) => {
    await page.goto('/questionario/1')
    // O campo de cidade deve estar visível
    await expect(page.getByLabel('Cidade')).toBeVisible()
  })
})
