/**
 * Testes E2E — Exportação (XLSX, CSV, PDF).
 *
 * Verifica que os links de download existem com hrefs corretos
 * e que o download do CSV retorna conteúdo não-vazio.
 */
import { test, expect } from '@playwright/test'
import { criarEnxoval } from './fixtures'

test.describe('Ajustes — seção Exportar', () => {
  test('links de exportação estão presentes com hrefs corretos', async ({ page }) => {
    const id = await criarEnxoval()
    await page.goto(`/enxoval/${id}/ajustes`)
    await page.waitForSelector('text=Curitiba', { timeout: 10_000 })

    const linkXlsx = page.getByRole('link', { name: /xlsx/i })
    const linkCsv = page.getByRole('link', { name: /csv/i })
    const linkPdf = page.getByRole('link', { name: /pdf/i })

    await expect(linkXlsx).toBeVisible()
    await expect(linkCsv).toBeVisible()
    await expect(linkPdf).toBeVisible()

    await expect(linkXlsx).toHaveAttribute('href', new RegExp(`${id}.*\\.xlsx`))
    await expect(linkCsv).toHaveAttribute('href', new RegExp(`${id}.*\\.csv`))
    await expect(linkPdf).toHaveAttribute('href', new RegExp(`${id}.*\\.pdf`))
  })

  test('links de exportação têm atributo download', async ({ page }) => {
    const id = await criarEnxoval()
    await page.goto(`/enxoval/${id}/ajustes`)
    await page.waitForSelector('text=Curitiba', { timeout: 10_000 })

    const links = [
      page.getByRole('link', { name: /xlsx/i }),
      page.getByRole('link', { name: /csv/i }),
      page.getByRole('link', { name: /pdf/i }),
    ]
    for (const link of links) {
      await expect(link).toHaveAttribute('download')
    }
  })

  test('download do CSV retorna conteúdo não-vazio', async ({ page, request }) => {
    const id = await criarEnxoval()

    // Faz o download diretamente via request (não via browser)
    const resposta = await request.get(`/api/v1/enxovais/${id}/exportar.csv`)
    expect(resposta.ok()).toBe(true)
    expect(resposta.headers()['content-type']).toContain('text/csv')

    const corpo = await resposta.text()
    expect(corpo.length).toBeGreaterThan(50)
    // Deve ter o cabeçalho esperado
    expect(corpo).toContain('Item')
  })

  test('download do XLSX retorna arquivo válido', async ({ page, request }) => {
    const id = await criarEnxoval()

    const resposta = await request.get(`/api/v1/enxovais/${id}/exportar.xlsx`)
    expect(resposta.ok()).toBe(true)
    expect(resposta.headers()['content-type']).toContain('spreadsheetml')

    const bytes = await resposta.body()
    // XLSX é um ZIP — começa com PK
    expect(bytes.slice(0, 2).toString()).toBe('PK')
  })

  test('download do PDF retorna arquivo válido', async ({ page, request }) => {
    const id = await criarEnxoval()

    const resposta = await request.get(`/api/v1/enxovais/${id}/exportar.pdf`)
    expect(resposta.ok()).toBe(true)
    expect(resposta.headers()['content-type']).toContain('application/pdf')

    const bytes = await resposta.body()
    expect(bytes.slice(0, 4).toString()).toBe('%PDF')
  })
})
