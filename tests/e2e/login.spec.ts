import { test, expect } from '@playwright/test';

test('login -> dashboard', async ({ page, baseURL }) => {
  await page.goto('/login');
  await page.getByLabel('Usuário').fill('admin');
  await page.getByLabel('Senha').fill('admin');
  await page.getByRole('button', { name: 'Entrar' }).click();
  await page.waitForURL('**/');
  await expect(page.locator('h1')).toHaveText(/Dashboard/i);
});

