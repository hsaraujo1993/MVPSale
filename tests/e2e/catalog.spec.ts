import { test, expect } from '@playwright/test';

async function auth(page){
  const resp = await page.request.post('/api/auth/token/', { data: { username: 'admin', password: 'admin' }});
  if (!resp.ok()) throw new Error('Unable to auth');
  const { access } = await resp.json();
  await page.addInitScript((token)=>{ localStorage.setItem('accessToken', token as string); }, access);
}

test('create, list and delete product', async ({ page }) => {
  await auth(page);
  await page.goto('/catalog');
  await page.getByRole('link', { name: 'Novo produto' }).click();
  await page.getByLabel('Nome').fill('Playwright Produto');
  await page.getByLabel('Preço de custo').fill('10');
  await page.getByLabel('Margem (%)').fill('20');
  await page.getByRole('button', { name: 'Salvar' }).click();

  // Should appear in list after reload performed by page script
  await page.waitForTimeout(500);
  await page.getByRole('button', { name: 'Aplicar' }).click();
  await expect(page.locator('#rows')).toContainText('Playwright Produto');

  // Delete the first matching row
  const delBtn = page.locator('#rows [data-del]').first();
  await delBtn.click();
  // Accept dialog
  page.once('dialog', d => d.accept());
  await page.waitForTimeout(500);
});

