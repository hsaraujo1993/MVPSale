# Frontend — MVPSale

Esta documentação descreve como executar a camada frontend (templates estáticos em "Novo Front") para desenvolvimento local e fornece uma checklist de QA por App pronta para uso.

Pré-requisitos
- Python 3.8+ (para o Django backend)
- Ambiente virtual ativado (recomendado: `.venv`)
- Dependências instaladas (ver `backend/requirements.txt`)
- Navegador moderno (Chrome, Edge, Firefox)

Como executar a aplicação localmente (frontend + backend)
1. No Windows (cmd.exe) a partir da raiz do repositório:

```cmd
cd "C:\Users\henri\Documents\Git_Projetos\MVPSale\backend"
.venv\Scripts\activate
python manage.py runserver
```

2. Abrir o frontend no navegador: http://localhost:8000/

Observações rápidas
- O diretório de templates do frontend fica em `Novo Front/templates` e é servido pelo Django a partir das views do projeto.
- Arquivos de scripts utilitários (p.ex. `Http.fetchJson`, `UI.confirm`, etc.) estão incluídos no template base e usados nas páginas.

Checklist de QA (por App)
- Catalog
  - [ ] Produtos: listagem, pesquisa (>=2 caracteres), paginação, criação, edição, exclusão, detalhe.
  - [ ] Marcas: listagem, criar/editar/excluir, detalhe. Verificar consistência de classes e botões.
  - [ ] Categorias: listagem, criar/editar/excluir.

- Stock
  - [ ] Listagem de estoques: verificação de nomes de produto (cache), paginação, detalhe com edição de mínimo/máximo.
  - [ ] Movimentações: listagem e filtros.

- People
  - [ ] Customers: criar/editar/excluir, pesquisa, paginação, detalhe com campos de contato.
  - [ ] Suppliers: criar/editar/excluir, pesquisa, problemas com CNPJ/razão social.
  - [ ] Sellers: criar/editar, permissões, desconto máximo.

- NFe (Notas fiscais)
  - [ ] Listagem de notas de fornecedor: filtros por número/série/fornecedor, paginação.
  - [ ] Importar XML: fluxo de upload/validação (se aplicável).

- Orders / Sales / Cashier
  - [ ] Pedidos: criação, adição de itens, edição de quantidades, finalização.
  - [ ] PDV: busca de produtos, adição ao pedido, seleção de cliente/vendedor, emissão NF-e.

- Payments
  - [ ] Métodos: criar/editar/excluir, taxas e prazos.
  - [ ] Recebíveis: filtros por status, visualização e conciliação.
  - [ ] Card brands & fees: criação e associação, validação de parcelas e taxas.

Como pedir ao Codex agents (FrontendDev / FrontendTest) para seguir com o desenvolvimento
- Garanta que ambos os agentes leiam os dois arquivos `README.md` (raiz) e `Novo Front/README_frontend.md`.
- Um comando prático que você pode fornecer ao agente executor para ler ambos os arquivos (no ambiente que o agente usa) é esta instrução (texto simples):

"Leia e analise `README.md` e `Novo Front/README_frontend.md` para entender o escopo do frontend e a checklist de QA. Priorize as páginas listadas em `Novo Front/templates` que não estejam padronizadas visualmente e crie PRs com pequenas mudanças por página (header/filtros/tabela/paginação)."

Sugestão de comando para agents automatizados (texto para colar no Codex agent prompt)

ReadFiles: README.md, "Novo Front/README_frontend.md"
Task: Standardize frontend list pages to use the same header/filters/table/pagination UI and produce PRs per app. Follow QA checklist in README_frontend.md.

---

Se quiser que eu adicione instruções de testes automatizados (p.ex. Playwright) ou gere scripts para executar testes E2E, eu posso incluir exemplos e um arquivo `playwright.config.ts` adaptado às rotas do projeto.

