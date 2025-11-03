Playwright E2E Setup

Prerequisitos
- Node 18+
- Python 3.10+ e backend rodando localmente

Passos
1) Inicie o backend em outro terminal:
   `python backend\manage.py runserver`

2) Garanta um usuário admin/admin (se ainda não existir):
   - `python backend\manage.py createsuperuser` e defina credenciais; ou
   - ajuste os testes para usar suas credenciais.

3) Instale dependências e rode e2e:
   - `npm i`
   - `npx playwright install --with-deps` (primeira vez)
   - `npm run test:e2e`

Config
- BaseURL: http://127.0.0.1:8000 (playwright.config.ts)
- Testes: tests/e2e/*.spec.ts
- Fixtures: tests/fixtures/

Observações
- Em CI os testes rodam headless por padrão.
- Se endpoints divergirem em sua instalação, ajuste as rotas nos testes ou use `page.route()` para mock de rede.

