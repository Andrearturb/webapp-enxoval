/**
 * Fixtures e helpers compartilhados entre os specs E2E.
 *
 * Uso principal: criar enxovais via API antes de um teste para não
 * precisar preencher o questionário completo em cada spec.
 */
import { request, type Page } from '@playwright/test'

const API_URL = process.env['API_URL'] ?? 'http://localhost:8010'

/** Corpo padrão do questionário — Curitiba, data futura, intermediário. */
export const RESPOSTAS_PADRAO = {
  municipio_codigo: 4106902,    // Curitiba/PR
  data_prevista: '2027-06-15',
  dias_entre_lavagens: 2,
  moradia: 'apartamento',
  tem_carro: true,
  orcamento: 'intermediario',
  primeiro_filho: true,
} as const

/**
 * Cria um enxoval via API REST e retorna o UUID.
 *
 * Preferir isso a preencher o questionário em cada teste — é mais rápido
 * e não depende da UI do questionário para testar outras páginas.
 */
export async function criarEnxoval(respostas = RESPOSTAS_PADRAO): Promise<string> {
  const ctx = await request.newContext({ baseURL: API_URL })
  const resp = await ctx.post('/api/v1/enxovais', { data: respostas })
  if (!resp.ok()) {
    throw new Error(`Falha ao criar enxoval: ${resp.status()} ${await resp.text()}`)
  }
  const { id } = await resp.json() as { id: string }
  await ctx.dispose()
  return id
}

/**
 * Navega para a planilha de um enxoval e aguarda os itens carregarem.
 *
 * @param page - Instância do Playwright Page.
 * @param id   - UUID do enxoval.
 */
export async function irParaPlanilha(page: Page, id: string): Promise<void> {
  await page.goto(`/enxoval/${id}/planilha`)
  // Aguarda ao menos um grupo de momento_compra aparecer
  await page.waitForSelector('[data-momento]', { timeout: 15_000 })
}

/**
 * Preenche o questionário completo via UI e retorna o UUID do enxoval criado.
 *
 * Seletores baseados na implementação real dos componentes:
 * - PassoCidade: input#cidade + buttons em ul>li
 * - Botões de avanço: "Avançar" (passos 1-5) e "Concluir" (passo 6)
 * - GrupoOpcoes: radio buttons com os rótulos exatos
 *
 * @param page - Instância do Playwright Page.
 */
export async function preencherQuestionario(page: Page): Promise<string> {
  await page.goto('/')

  // Clica no link "Começar meu enxoval" da página inicial (primeiro = hero)
  await page.getByRole('link', { name: /começar meu enxoval/i }).first().click()

  // Passo 1 — Cidade
  await page.waitForURL(/\/questionario\/1/)
  await page.getByLabel('Cidade').fill('Curitiba')
  // Os resultados são <button> dentro de <li>, não <option>
  await page.waitForSelector('ul li button', { timeout: 10_000 })
  await page.locator('ul li button').filter({ hasText: /Curitiba.*PR/i }).first().click()
  await page.getByRole('button', { name: 'Avançar' }).click()

  // Passo 2 — Data prevista
  await page.waitForURL(/\/questionario\/2/)
  await page.getByLabel(/data prevista/i).fill('2027-06-15')
  await page.getByRole('button', { name: 'Avançar' }).click()

  // Passo 3 — Frequência de lavagem (rótulo exato do GrupoOpcoes)
  await page.waitForURL(/\/questionario\/3/)
  await page.getByRole('radio', { name: 'Lavo a cada 2 dias' }).click()
  await page.getByRole('button', { name: 'Avançar' }).click()

  // Passo 4 — Moradia e carro (rótulos exatos)
  await page.waitForURL(/\/questionario\/4/)
  await page.getByRole('radio', { name: 'Apartamento' }).click()
  await page.getByRole('radio', { name: 'Sim' }).click()
  await page.getByRole('button', { name: 'Avançar' }).click()

  // Passo 5 — Orçamento
  await page.waitForURL(/\/questionario\/5/)
  await page.getByRole('radio', { name: /intermediário/i }).click()
  await page.getByRole('button', { name: 'Avançar' }).click()

  // Passo 6 — Primeiro filho
  await page.waitForURL(/\/questionario\/6/)
  await page.getByRole('radio', { name: 'Sim' }).click()
  await page.getByRole('button', { name: 'Concluir' }).click()

  // Aguarda redirecionar para a planilha
  await page.waitForURL(/\/enxoval\/.+\/planilha/, { timeout: 15_000 })

  // Extrai o UUID da URL
  const match = page.url().match(/\/enxoval\/([^/]+)\/planilha/)
  if (!match) throw new Error(`URL inesperada após questionário: ${page.url()}`)
  return match[1]
}
