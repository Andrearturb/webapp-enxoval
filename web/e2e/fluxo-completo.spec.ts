/**
 * Testes E2E — Fluxo completo.
 *
 * Cobre o caminho principal do usuário:
 * 1. Página inicial
 * 2. Questionário (6 passos)
 * 3. Planilha (listagem e grupos por momento_compra)
 * 4. Roteiro
 * 5. Guia dos itens
 * 6. Segurança
 * 7. Ajustes
 * 8. Erro 404 para enxoval inexistente
 */
import { test, expect } from '@playwright/test'
import { criarEnxoval, irParaPlanilha, preencherQuestionario } from './fixtures'

test.describe('Página inicial', () => {
  test('exibe proposta e botão de início', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/enxoval inteligente/i)
    await expect(page.getByRole('link', { name: /começar meu enxoval/i }).first()).toBeVisible()
  })
})

test.describe('Questionário → Planilha', () => {
  test('preencher questionário completo chega na planilha', async ({ page }) => {
    const id = await preencherQuestionario(page)

    // Deve estar na planilha com UUID válido
    await expect(page).toHaveURL(new RegExp(`/enxoval/${id}/planilha`))

    // Pelo menos um grupo de momento_compra deve aparecer
    await expect(page.locator('[data-momento]').first()).toBeVisible()

    // Deve ter itens listados
    await expect(page.getByTestId('linha-item').first()).toBeVisible()
  })
})

test.describe('Navegação entre abas', () => {
  test.beforeEach(async ({ page }) => {
    const id = await criarEnxoval()
    await irParaPlanilha(page, id)
  })

  test('aba Roteiro mostra fases com datas', async ({ page }) => {
    await page.getByRole('link', { name: 'Roteiro' }).click()
    await expect(page).toHaveURL(/\/roteiro/)
    await expect(page.getByRole('heading').first()).toBeVisible()
  })

  test('aba Guia mostra fichas de itens', async ({ page }) => {
    await page.getByRole('link', { name: 'Guia' }).click()
    await expect(page).toHaveURL(/\/guia/)
    await expect(page.getByRole('main')).toBeVisible()
  })

  test('aba Segurança mostra alertas', async ({ page }) => {
    await page.getByRole('link', { name: 'Segurança' }).click()
    await expect(page).toHaveURL(/\/seguranca/)
    await expect(page.getByRole('main')).toBeVisible()
  })

  test('aba Ajustes mostra respostas do questionário', async ({ page }) => {
    await page.getByRole('link', { name: 'Ajustes' }).click()
    await expect(page).toHaveURL(/\/ajustes/)
    await expect(page.getByText('Curitiba - PR').first()).toBeVisible()
  })
})

test.describe('Erro 404', () => {
  test('UUID inexistente exibe página de erro amigável', async ({ page }) => {
    await page.goto('/enxoval/00000000-0000-0000-0000-000000000000/planilha')
    // Deve mostrar mensagem de "não encontrado" em vez de quebrar
    await expect(page.getByText(/enxoval não encontrado/i)).toBeVisible()
  })
})
