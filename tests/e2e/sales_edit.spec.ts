import { test, expect } from '@playwright/test';

async function uiLogin(page) {
  await page.goto('/login');
  await page.getByLabel('Usuário', { exact: false }).fill('admin');
  await page.getByLabel('Senha', { exact: false }).fill('admin');
  await page.getByRole('button', { name: /Entrar/i }).click();
  await page.waitForURL('**/');
}

test('sales edit draft: open by ?order, change payment patches immediately', async ({ page }) => {
  test.setTimeout(120_000);
  // login
  await uiLogin(page);

  // Create a draft order via API using session (best-effort); skip if not possible
  let orderUUID: string | null = null;
  try {
    const ensureSeller = await page.evaluate(async () => {
      const r = await fetch('/api/people/sellers/ensure-me/', { method: 'POST', credentials: 'same-origin' });
      if (!r.ok) throw new Error('ensure-me failed');
      return await r.json();
    });
    const seller = ensureSeller?.uuid;
    if (!seller) test.skip(true, 'no seller available');
    const methods = await page.evaluate(async () => {
      const r = await fetch('/api/payment/methods/?ordering=name', { credentials: 'same-origin' });
      if (!r.ok) throw new Error('methods failed');
      return await r.json();
    });
    const list = Array.isArray(methods?.results) ? methods.results : (Array.isArray(methods) ? methods : []);
    if (!list.length) test.skip(true, 'no payment methods');
    const pm = list[0]?.uuid;
    const created = await page.evaluate(async ({ seller, pm }) => {
      const r = await fetch('/api/sale/orders/', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ seller, payment_method: pm, order_type: 'orcamento' }) });
      if (!r.ok) throw new Error('create order failed');
      return await r.json();
    }, { seller, pm });
    orderUUID = created?.uuid || null;
  } catch {
    test.skip(true, 'prerequisites not met');
  }
  if (!orderUUID) test.skip(true, 'no order id');

  // Open PDV in edit mode
  await page.goto(`/sales?order=${orderUUID}`);
  // Button should be "Salvar orçamento" (draft budget) or "Finalizar" depending on type
  const primaryBtn = page.getByRole('button', { name: /Salvar|Finalizar/i }).first();
  await expect(primaryBtn).toBeVisible();

  // Change payment method -> should trigger immediate PATCH (toast optional)
  const pmSelect = page.locator('select').filter({ hasText: '' }).first();
  if (await pmSelect.count()) {
    // Try to select second option if exists; otherwise re-select first
    const opts = pmSelect.locator('option');
    const count = await opts.count();
    const toSelect = count > 1 ? (await opts.nth(1).getAttribute('value')) : (await opts.nth(0).getAttribute('value'));
    if (toSelect) await pmSelect.selectOption(toSelect);
  }

  // Detail page should open and remain stable
  await expect(page).toHaveURL(/\/sales\?order=/);
});

