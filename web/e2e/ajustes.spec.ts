import { expect, test } from '@playwright/test'
import { checkA11y, injectAxe } from 'axe-playwright'
import { criarEnxoval } from './fixtures'

test('edita respostas, preserva registros e restaura itens fora da recomendação', async ({
  page,
}) => {
  test.slow() // Três recálculos completos e verificações de acessibilidade.
  const id = await criarEnxoval()
  const url = `/api/v1/enxovais/${id}`
  const marca = { comprada: 20, ganhada: 3, ja_tinha: 2 }
  try {
    expect(
      (await page.request.put(`${url}/linhas/gorro:P:`, { data: marca })).ok(),
    ).toBeTruthy()
    await page.goto(`/enxoval/${id}/ajustes`)
    await page.getByRole('button', { name: 'Editar respostas' }).click()
    await expect(page.getByLabel('Cidade')).toHaveValue('Curitiba - PR')
    await expect(
      page.getByRole('button', { name: 'Revisar alterações' }),
    ).toBeDisabled()
    await page.getByRole('radio', { name: 'Investir mais' }).click()
    await injectAxe(page)
    await checkA11y(page, undefined, {
      includedImpacts: ['critical', 'serious'],
    })
    await page.getByRole('button', { name: 'Revisar alterações' }).click()
    await expect(
      page.getByRole('heading', { name: 'Confira seu enxoval atualizado' }),
    ).toBeVisible()
    expect(
      (await (await page.request.get(url)).json()).respostas.orcamento,
    ).toBe('intermediario')
    await checkA11y(page, undefined, {
      includedImpacts: ['critical', 'serious'],
    })
    await page
      .getByRole('button', { name: 'Confirmar e atualizar enxoval' })
      .click()
    await expect(page.getByRole('status')).toContainText('Enxoval atualizado')
    const atualizado = await (await page.request.get(url)).json()
    expect(atualizado.id).toBe(id)
    expect(atualizado.respostas.orcamento).toBe('investir')
    const gorro = atualizado.linhas.find(
      (l: { chave: string }) => l.chave === 'gorro:P:',
    )
    expect(gorro).toMatchObject(marca)

    // Mudar de cidade remove roupas de frio, mantendo as marcações acessíveis.
    await page.getByRole('button', { name: 'Editar respostas' }).click()
    await page.getByLabel('Cidade').fill('Salvador')
    await page
      .getByRole('button', { name: 'Salvador - BA', exact: true })
      .click()
    await page.getByRole('button', { name: 'Revisar alterações' }).click()
    await page
      .getByRole('button', { name: 'Confirmar e atualizar enxoval' })
      .click()
    await expect(page.getByRole('status')).toContainText('Enxoval atualizado')
    await page.getByRole('link', { name: 'Planilha', exact: true }).click()
    const fora = page.getByRole('region', {
      name: 'Fora da recomendação atual',
    })
    await expect(fora).toContainText('Comprei: 20 · Ganhei: 3 · Já tinha: 2')
    await injectAxe(page)
    await checkA11y(page, undefined, {
      includedImpacts: ['critical', 'serious'],
    })

    // Voltar à cidade anterior recupera as marcações na lista recomendada.
    await page.getByRole('link', { name: 'Ajustes', exact: true }).click()
    await page.getByRole('button', { name: 'Editar respostas' }).click()
    await page.getByLabel('Cidade').fill('Curitiba')
    await page
      .getByRole('button', { name: 'Curitiba - PR', exact: true })
      .click()
    await page.getByRole('button', { name: 'Revisar alterações' }).click()
    await page
      .getByRole('button', { name: 'Confirmar e atualizar enxoval' })
      .click()
    await expect(page.getByRole('status')).toContainText('Enxoval atualizado')
    const restaurado = await (await page.request.get(url)).json()
    expect(
      restaurado.linhas.find((l: { chave: string }) => l.chave === 'gorro:P:'),
    ).toMatchObject(marca)
    expect(restaurado.linhas_fora_da_lista).toEqual([])
  } finally {
    await page.request.delete(url)
  }
})
