import { test, expect } from '@playwright/test';

async function login(page) {
  await page.goto('/login');
  await page.locator('input[name="username"]').fill('admin');
  await page.locator('input[name="password"]').fill('admin');
  await page.getByRole('button', { name: /Entrar/i }).click();
  await page.waitForURL('**/');
}

test.describe('Admin > Revisão de Preço', () => {
  test('submenu aparece (no DOM) e navega para a tela', async ({ page }) => {
    await login(page);
    await page.goto('/catalog');
    // Verifica que o atalho existe no DOM (independente de visibilidade/responsivo)
    const adminLink = page.locator('a[href="/price-review"]');
    await expect(await adminLink.count()).toBeGreaterThan(0);
    // Navega diretamente para a tela
    await page.goto('/price-review');
    await expect(page).toHaveURL(/\/price-review$/);
    await expect(page.locator('h1')).toHaveText(/Revis(ã|a)o de Pre(ç|c)o/i);
  });
});
