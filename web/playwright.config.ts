/**
 * Configuração do Playwright para testes E2E.
 *
 * Roda contra a stack local (docker compose up) com o frontend em
 * http://localhost:5180 (ou BASE_URL via variável de ambiente no Docker).
 *
 * Projetos:
 * - chromium: fluxo completo + acessibilidade (desktop)
 * - mobile-chrome: fluxo completo em viewport iPhone 14
 * - firefox: smoke test do fluxo completo
 */
import { defineConfig, devices } from '@playwright/test'

const BASE_URL = process.env['BASE_URL'] ?? 'http://localhost:5180'

export default defineConfig({
  // Pasta onde ficam os specs E2E
  testDir: './e2e',

  // Captura screenshot em falhas e salva trace para debug
  use: {
    baseURL: BASE_URL,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },

  // Número de retentativas em CI para reduzir flakiness
  retries: process.env['CI'] ? 2 : 0,

  // Timeout generoso pois a API pode estar cold-starting
  timeout: 30_000,
  expect: { timeout: 10_000 },

  // Relatório: lista no terminal + HTML para debug
  reporter: [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]],

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 7'] },
    },
  ],
})
