# 🚀 Frontend em Django Templates consumindo DRF

## Contexto

Você é FrontendDev. Gere um frontend moderno em Django Templates que consome as APIs do Django REST Framework já existentes. Use Tailwind CSS (via CDN), Alpine.js para interações básicas, lucide-react (SVG inline ou CDN) para ícones, e dark mode por padrão. A aplicação inicia na tela de login (mock: `admin` / `admin`), e roda com `python manage.py runserver`.

---

## Stack / UI

- Django Templates + Tailwind via CDN + Alpine.js (sem build step).
- Dark mode por padrão com gradientes harmônicos; tipografia limpa; cards com cantos arredondados; sombras suaves.
- Componentes reutilizáveis: `base.html`, `partials/navbar.html`, `partials/sidebar.html`, `partials/alerts.html`, `partials/pagination.html`, `partials/form_field.html`, `partials/confirm_modal.html`.

---

## Premissas sobre as APIs DRF

- Prefixo de API: `/api/` (ex.: `/api/products/`, `/api/categories/`, etc.).
- Autenticação: sessão Django. Use CSRF token com `fetch` para POST/PUT/PATCH/DELETE.
- Todas as listas devem suportar paginação, busca e ordenação (query params `?search=&ordering=&page=`).

---

## Estrutura de navegação (menu)

- Catálogo
  - Produto
  - Categoria
  - Marca
  - Estoque
- Pessoas / Cadastros
  - Clientes
  - Fornecedores
  - Vendedores
- Notas Fiscais
  - Notas emitidas pelo sistema
  - Notas de fornecedores (com upload de XML)
- Caixa
  - Abrir o Caixa (tela simples com status do dia e ação de abertura/fechamento)
- Pedidos
  - Listar Pedidos (filtros por status, data, cliente, vendedor)
- Administrativo
  - Pagamentos (Bandeiras, Formas, Taxas)
  - Pagamentos recebidos
  - Controle de Saída e Entrada de Estoque
- Dashboard
  - Integração com APIs de auditoria (cards de indicadores, gráfico simples com `<canvas>`)

---

## Páginas e templates (entregáveis)

Para cada recurso modelado acima, criar:

- `list.html` — tabela com: filtros (busca, ordenação, status), paginação padrão, ações (ver, editar, excluir).
- `detail.html` — visão de leitura, com resumo em cards e seção de metadados/auditoria.
- `form.html` — criação/edição com validação inline, placeholders, help-text, tooltips e máscaras quando aplicável.

Páginas específicas com requisitos:

- **Login** (`auth/login.html`): card central, dark friendly, gradiente no header, ícone. Mock credenciais: `user: admin` / `password: admin`. Redirecionar para Dashboard após login.

- **Notas de Fornecedores** (`nfe/supplier_invoices/form.html`): campo Upload XML (input file) + preview dos metadados extraídos (após upload, parse no backend; exibir retorno da API). Mostrar campos mapeados essenciais (CNPJ, chave, data, produtos com NCM/CFOP/CST, código de barras, códigos OEM/vendedor, tributos). Ação “Enviar” faz `POST` para `/api/supplier-invoices/`. Em caso de erro de parse, exibir alert padronizado com detalhamento.

- **Dashboard** (`dashboard/index.html`): cards com KPIs (ex.: pedidos no dia, faturamento, tíquete médio, estoque crítico), lista de “Eventos de Auditoria Recentes” (consome endpoint de auditoria) e um pequeno gráfico (HTML `<canvas>`) alimentado pelos dados de auditoria.

- **Caixa** (`cashier/open.html`): exibir status atual (aberto/fechado, horário, operador). Ações: Abrir Caixa / Fechar Caixa (`POST` na API). Tabela de movimentos do dia (entradas/saídas) com somatórios.

---

## Componentização & Reutilização

- `base.html`: inclui Tailwind (CDN), Alpine, scripts de CSRF, toasts/alerts globais, container responsivo, dark mode.
- `partials/navbar.html` e `partials/sidebar.html`: menu com grupos conforme navegação; ícones lucide SVG inline.
- `partials/form_field.html`: partial para renderizar label + input + help + error.
- `partials/pagination.html`: controles de página com acessibilidade.
- `partials/alerts.html`: toasts (sucesso/erro) e banners de página.

---

## Acessibilidade & Responsividade

- Mobile-first; grid responsivo nas tabelas (overflow-x com sticky header no mobile).
- Use `aria-*` nos botões de ação e modais; gerencie foco ao abrir modais.
- Garanta contraste adequado no dark mode e tamanho de fonte confortável.

---

## Integração com API (padrões JS)

- Criar helper `fetchJson(url, options)` com padrão de cabeçalhos:
  - `Accept: application/json`
  - `X-CSRFToken: {{ csrf_token }}` (injetado no template)
- Tratamento centralizado de erros (HTTP e `detail` do DRF).
- Todas as telas de list: ler de `/api/<recurso>/?search=&ordering=&page=` e preencher tabela.
- `form.html`: realizar `POST`/`PUT`/`PATCH`; exibir validações do serializer no campo correspondente.
- `delete`: modal de confirmação → `DELETE` → toast de sucesso e refresh.

---

## Estilo visual

- Dark mode padrão; toggle para light.
- Gradientes harmônicos nos headers/cards (ex.: roxos/azuis/esverdeados suaves).
- Animações discretas (hover em cards/botões; transições em modais).
- Ícones lucide em botões de ação (add, edit, delete, upload, filter, search).

---

## Estrutura de pastas sugerida

```
templates/
  base.html
  auth/login.html
  dashboard/index.html
  partials/
    navbar.html
    sidebar.html
    alerts.html
    pagination.html
    form_field.html
    confirm_modal.html
  catalog/
    product/list.html
    product/detail.html
    product/form.html
    category/... 
  people/
    customers/...
    suppliers/...
    sellers/...
  nfe/
    supplier_invoices/list.html
    supplier_invoices/detail.html
    supplier_invoices/form.html
  cashier/open.html
  orders/list.html
static/
  js/csrf.js
  js/http.js        # fetchJson helper + handlers
  js/ui.js          # toasts, modals, skeletons
  css/custom.css
```

---

## Entregáveis

- Todos os templates (list/detail/form) para cada recurso listado.
- Base de layout com dark mode, gradientes e componentes parciais.
- Helpers JS (`fetchJson`, tratamento de erros, toasts, modal).
- Padrão de alertas unificado e reutilizável.
- Upload de XML funcional em Notas de Fornecedores + preview dos dados retornados.
- Dashboard com KPIs e eventos de auditoria.
- Página do Caixa com abertura/fechamento e movimentos.
- Documentação curta em `README_frontend.md` explicando como rodar (incluir “rodar com `python manage.py runserver`” e credenciais mock de login).

---

## Critérios de Aceite (QA / FrontendTest)

- Navegação funciona e preserva sessão após login mock.
- Todas as listas paginam, ordenam, buscam e tratam erros da API graciosamente.
- Formulários validam campos obrigatórios, exibem erros do DRF no campo exato e mostram toasts uniformes.
- Upload XML: aceita `.xml`, retorna preview, bloqueia tipos incorretos e mostra erro corretamente.
- Responsividade (320px, 768px, 1024px, 1440px) sem overflow visual crítico.
- Acessibilidade: labels associados, foco visível, `aria` em modais, contraste suficiente no dark.
- Sem erros de JS no console em fluxos principais.
- Dashboard carrega KPIs e eventos; falhas da API exibem estado de erro amigável.

---

## Saídas do FrontendTest (sugestão)

- `tests/e2e/*.spec.ts` (ou `.js`) com cenários críticos (Playwright recomendado).
- `frontend_review.log` com:
  - Bugs encontrados (com passos para reproduzir).
  - Melhorias de UX/UI.
  - Sugestões de refatoração (componentização, helpers, acessibilidade).

---

## Observações finais

- Use ícones modernos e descrições claras nos inputs.
- Garanta consistência visual entre todas as páginas.
- Não introduzir dependências que exijam build; manter CDN para bibliotecas.
- Onde faltar endpoint exato, isole em constantes no topo do template/JS para fácil ajuste.

---

## Execução

Rodar o servidor Django a partir do diretório apropriado:

```bash
python manage.py runserver
```

Login (mock): `user: admin` / `password: admin`

---

## Guia rápido adicional

Veja também o arquivo separado com instruções de execução rápidas e checklist de QA:

- `README_frontend.md` — guia prático com comandos para rodar, checklist de QA e sugestões de automação (Playwright).

> Nota: documentação específica do frontend (instruções de execução local e checklist de QA por App) também está disponível em `Novo Front/README_frontend.md`.
