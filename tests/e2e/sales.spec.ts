import { test, expect, request } from '@playwright/test';

const USERNAME = process.env.E2E_USER || 'dev';
const PASSWORD = process.env.E2E_PASS || 'dev12345';

async function apiAuth(baseURL: string) {
  const ctx = await request.newContext({ baseURL });
  const resp = await ctx.post('/api/token/', {
    data: { username: USERNAME, password: PASSWORD },
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
  });
  expect(resp.ok()).toBeTruthy();
  const json = await resp.json();
  return { ctx, access: json.access as string };
}

test.describe('Sales page (PDV)', () => {
  test('updates quantity with PATCH and updates total; discount reflects', async ({ page, baseURL }) => {
    // Seed minimal catalog via API
    const { ctx, access } = await apiAuth(baseURL!);
    const auth = { Authorization: `Bearer ${access}`, 'Content-Type': 'application/json', Accept: 'application/json' };

    const cat = await (await ctx.post('/api/catalog/categories/', { data: { name: 'E2E Cat' }, headers: auth })).json();
    const brand = await (await ctx.post('/api/catalog/brands/', { data: { name: 'E2E Brand' }, headers: auth })).json();
    const prod = await (await ctx.post('/api/catalog/products/', {
      data: { name: 'E2E Product 1', description: 'p1', category: cat.uuid, brand: brand.uuid, cost_price: 80, margin: 5, active: true }, headers: auth,
    })).json();

    // Login via UI
    await page.goto('/login');
    await page.locator('input[name="username"]').fill(USERNAME);
    await page.locator('input[name="password"]').fill(PASSWORD);
    await page.getByRole('button', { name: /Entrar/i }).click();

    // Go to Sales and add the product
    await page.goto('/sales');
    await page.locator('input[x-model="search"]').fill('E2E Product 1');
    const productsResp = page.waitForResponse(/\/api\/catalog\/products/);
    await page.keyboard.press('Enter');
    await productsResp;
    const productRow = page.locator('tbody tr', { hasText: 'E2E Product 1' }).first();
    await expect(productRow).toBeVisible();
    await productRow.getByRole('button', { name: 'Adicionar' }).click();

    // Capture non-GET requests during quantity update
    const nonGet: { method: string; url: string; body?: any; }[] = [];
    page.on('request', r => {
      if (r.method() !== 'GET') nonGet.push({ method: r.method(), url: r.url() });
    });

    // Update quantity from 1 to 2
    const itemsRow = page.locator('table', { hasText: 'Desc. %' }).locator('tr', { hasText: 'E2E Product 1' }).first();
    const qtyInput = itemsRow.locator('input[type="number"]:not([readonly])').first();
    await qtyInput.fill('2');
    await qtyInput.blur();

    // Assert we sent a PATCH to the correct endpoint
    await expect.poll(() => nonGet.find(n => /\/api\/sale\/orders\/.+\/items\/.+\/$/.test(n.url))?.method).toContain('PATCH');

    // Capture total before and after discount
    const totalEl = page.locator('text=Total:').locator('xpath=following-sibling::span');
    const totalBefore = await totalEl.innerText();

    // Apply general discount 10%
    const discountGeneral = page.locator('label:has-text("Desconto geral")').locator('..').locator('input');
    await discountGeneral.fill('10');
    await discountGeneral.blur();

    await expect.poll(async () => (await totalEl.innerText()) !== totalBefore).toBeTruthy();
  });

  test('insufficient stock adjusts to 1; subsequent valid change patches successfully', async ({ page, baseURL }) => {
    // Seed minimal catalog via API
    const { ctx, access } = await apiAuth(baseURL!);
    const auth = { Authorization: `Bearer ${access}`, 'Content-Type': 'application/json', Accept: 'application/json' };

    const cat = await (await ctx.post('/api/catalog/categories/', { data: { name: 'E2E Cat S' }, headers: auth })).json();
    const brand = await (await ctx.post('/api/catalog/brands/', { data: { name: 'E2E Brand S' }, headers: auth })).json();
    const prod = await (await ctx.post('/api/catalog/products/', {
      data: { name: 'E2E Product S', description: 'ps', category: cat.uuid, brand: brand.uuid, cost_price: 50, margin: 10, active: true }, headers: auth,
    })).json();

    // Intercept stock lookup to force stock = 1 for any product
    await page.route(/\/api\/stock\/\?product__uuid=.*/, route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [{ quantity_current: 1 }] }),
      });
    });

    // Login via UI
    await page.goto('/login');
    await page.locator('input[name="username"]').fill(USERNAME);
    await page.locator('input[name="password"]').fill(PASSWORD);
    await page.getByRole('button', { name: /Entrar/i }).click();

    // Go to Sales and add the product
    await page.goto('/sales');
    await page.locator('input[x-model="search"]').fill('E2E Product S');
    const productsResp = page.waitForResponse(/\/api\/catalog\/products/);
    await page.keyboard.press('Enter');
    await productsResp;
    const productRow = page.locator('tbody tr', { hasText: 'E2E Product S' }).first();
    await expect(productRow).toBeVisible();
    await productRow.getByRole('button', { name: 'Adicionar' }).click();

    // Track network
    const nonGet: { method: string; url: string; status?: number }[] = [];
    page.on('request', r => { if (r.method() !== 'GET') nonGet.push({ method: r.method(), url: r.url() }); });
    const responses: { url: string; status: number }[] = [];
    page.on('response', r => { responses.push({ url: r.url(), status: r.status() }); });

    // Set quantity to 3 (above stock 1) -> expect UI warn and auto adjust to 1
    const itemsRow = page.locator('table', { hasText: 'Desc. %' }).locator('tr', { hasText: 'E2E Product S' }).first();
    const qtyInput = itemsRow.locator('input[type="number"]:not([readonly])').first();
    await qtyInput.fill('3');
    await qtyInput.blur();
    await expect(itemsRow.locator('text=Quantidade ajustada para 1')).toBeVisible();

    // Change to valid quantity 1 (<= stock after warn)
    await qtyInput.fill('1');
    await qtyInput.blur();

    // Assert we sent a PATCH to items endpoint and did not hit 405
    await expect.poll(() => nonGet.find(n => /\/api\/sale\/orders\/.+\/items\/.+\/$/.test(n.url))?.method).toContain('PATCH');
    const itemResponses = responses.filter(r => /\/api\/sale\/orders\/.+\/items\/.+\/$/.test(r.url));
    expect(itemResponses.find(r => r.status === 405)).toBeFalsy();
  });

  test('blocks adding product with price 0 and shows hint; opens catalog', async ({ page, baseURL }) => {
    const { ctx, access } = await apiAuth(baseURL!);
    const auth = { Authorization: `Bearer ${access}`, 'Content-Type': 'application/json', Accept: 'application/json' };

    const cat = await (await ctx.post('/api/catalog/categories/', { data: { name: 'E2E Cat 0' }, headers: auth })).json();
    const brand = await (await ctx.post('/api/catalog/brands/', { data: { name: 'E2E Brand 0' }, headers: auth })).json();
    await (await ctx.post('/api/catalog/products/', {
      data: { name: 'E2E Product 0', description: 'p0', category: cat.uuid, brand: brand.uuid, cost_price: 0, margin: 0, active: true }, headers: auth,
    })).json();

    await page.goto('/login');
    await page.locator('input[name="username"]').fill(USERNAME);
    await page.locator('input[name="password"]').fill(PASSWORD);
    await page.getByRole('button', { name: /Entrar/i }).click();

    await page.goto('/sales');
    await page.locator('input[x-model="search"]').fill('E2E Product 0');
    const resp0 = page.waitForResponse(/\/api\/catalog\/products/);
    await page.keyboard.press('Enter');
    await resp0;
    const row0 = page.locator('tbody tr', { hasText: 'E2E Product 0' }).first();
    await expect(row0).toBeVisible();
    const semPreco = row0.getByRole('button', { name: 'Sem preço' }).first();
    await expect(semPreco).toBeVisible();

    const [newPage] = await Promise.all([
      page.context().waitForEvent('page'),
      semPreco.click(),
    ]);
    await newPage.waitForLoadState('domcontentloaded');
    await expect(newPage).toHaveURL(/\/catalog\?tab=products/);
  });

  test('shows brand and installments when selecting credit card', async ({ page, baseURL }) => {
    const { ctx, access } = await apiAuth(baseURL!);
    const auth = { Authorization: `Bearer ${access}`, 'Content-Type': 'application/json', Accept: 'application/json' };

    // Ensure a credit card payment method exists
    const pm = await (await ctx.post('/api/payment/methods/', { data: { code: 'visa', name: 'Cartão Crédito Visa', type: 'card_credit' }, headers: auth })).json();
    // Ensure a card brand and a fee tier for 1..6x
    const brand = await (await ctx.post('/api/payment/card-brands/', { data: { name: 'Visa' }, headers: auth })).json();
    await ctx.post('/api/payment/card-fees/', { data: { brand: brand.id, type: 'card_credit', installments_min: 1, installments_max: 6, fee_percent: 2.5, settlement_days: 30 }, headers: auth });

    await page.goto('/login');
    await page.locator('input[name="username"]').fill(USERNAME);
    await page.locator('input[name="password"]').fill(PASSWORD);
    await page.getByRole('button', { name: /Entrar/i }).click();

    await page.goto('/sales');
    const formaBtn = page.locator('label:has-text("Forma de pagamento")').locator('..').getByRole('button');
    await formaBtn.click();
    await page.selectOption('select[x-model="payment_method"]', pm.uuid);

    // Expect brand and installments controls
    await expect(page.locator('label:has-text("Bandeira")')).toBeVisible();
    await page.selectOption('select[x-model="cardBrand"]', String(brand.id));
    const brandSelect = page.locator('select[x-model="cardBrand"]');
    await expect(brandSelect).toBeVisible();
    await page.selectOption(brandSelect, String(brand.id));
    const options = page.locator('select[x-model="installments"] option');
    await expect(options.count()).resolves.toBeGreaterThanOrEqual(6);
  });

  test('breakdown: subtotal, discounts, fee and total are correct', async ({ page, baseURL }) => {
    const { ctx, access } = await apiAuth(baseURL!);
    const auth = { Authorization: `Bearer ${access}`, 'Content-Type': 'application/json', Accept: 'application/json' };

    // Seed payment method (card credit), brand and tier (1x @ 2%)
    const pm = await (await ctx.post('/api/payment/methods/', { data: { code: 'visa2', name: 'Cartão Crédito Visa', type: 'card_credit' }, headers: auth })).json();
    const brand = await (await ctx.post('/api/payment/card-brands/', { data: { name: 'Visa' }, headers: auth })).json();
    await ctx.post('/api/payment/card-fees/', { data: { brand: brand.id, type: 'card_credit', installments_min: 1, installments_max: 1, fee_percent: 2.0, settlement_days: 30 }, headers: auth });

    // Seed product with sale_price ~= 100 (cost 50, margin 100%)
    const cat = await (await ctx.post('/api/catalog/categories/', { data: { name: 'E2E Totals Cat' }, headers: auth })).json();
    const br = await (await ctx.post('/api/catalog/brands/', { data: { name: 'E2E Totals Brand' }, headers: auth })).json();
    const prod = await (await ctx.post('/api/catalog/products/', {
      data: { name: 'E2E Totals Product', description: 'pT', category: cat.uuid, brand: br.uuid, cost_price: 50, margin: 100, active: true }, headers: auth,
    })).json();

    // Login and go to Sales
    await page.goto('/login');
    await page.locator('input[name="username"]').fill(USERNAME);
    await page.locator('input[name="password"]').fill(PASSWORD);
    await page.getByRole('button', { name: /Entrar/i }).click();

    await page.goto('/sales');
    await page.locator('input[x-model="search"]').fill('E2E Totals Product');
    const resp = page.waitForResponse(/\/api\/catalog\/products/);
    await page.keyboard.press('Enter');
    await resp;
    // Click 'Adicionar' (list can re-render; pick the first visible button)
    await page.getByRole('button', { name: 'Adicionar' }).first().click();

    // Select payment method and brand; ensure card credit and tier apply (1x @2%)
    const formaBtn = page.locator('label:has-text("Forma de pagamento")').locator('..').getByRole('button');
    await formaBtn.click();
    await page.selectOption('select[x-model="payment_method"]', pm.uuid);
    await page.selectOption('select[x-model="cardBrand"]', String(brand.id));

    // Set item discount % = 10
    const itemsRow = page.locator('table', { hasText: 'Desc. %' }).locator('tr', { hasText: 'E2E Totals Product' }).first();
    const inputs = itemsRow.locator('input[type="number"]:not([readonly])');
    await inputs.nth(1).fill('10'); // discount_percent field
    await inputs.nth(1).blur();

    // Set order discounts: % = 10, valor = 5
    const discPerc = page.locator('label:has-text("Desconto geral (%)")').locator('..').locator('input');
    await discPerc.fill('10');
    await discPerc.blur();
    const discAbs = page.locator('label:has-text("Desconto geral (valor)")').locator('..').locator('input');
    await discAbs.fill('5');
    await discAbs.blur();

    // Validate breakdown
    await expect(page.locator('text=Subtotal:').locator('xpath=following-sibling::span')).toContainText('100.00');
    await expect(page.locator('text=Desconto aplicado:').locator('xpath=following-sibling::span')).toContainText('24.00');
    await expect(page.locator('text=Taxa Cartão:')).toContainText('2.00%');
    await expect(page.locator('text=Valor juros:').locator('xpath=following-sibling::span')).toContainText('1.52');
    await expect(page.locator('text=Valor total:').locator('xpath=following-sibling::span')).toContainText('77.52');
  });
});
