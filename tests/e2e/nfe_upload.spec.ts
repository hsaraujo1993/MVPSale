import { test, expect } from '@playwright/test';

async function auth(page){
  const resp = await page.request.post('/api/auth/token/', { data: { username: 'admin', password: 'admin' }});
  if (!resp.ok()) throw new Error('Unable to auth');
  const { access } = await resp.json();
  await page.addInitScript((token)=>{ localStorage.setItem('accessToken', token as string); }, access);
}

test('upload XML and preview shows', async ({ page }) => {
  await auth(page);
  await page.goto('/nfe');
  const file = 'tests/fixtures/sample_invoice.xml';
  await page.setInputFiles('input[type=file][name=xml]', file);
  await page.getByRole('button', { name: 'Enviar' }).click();
  await expect(page.locator('#preview')).toBeVisible();
  await expect(page.locator('#previewJson')).toContainText('status');
});

