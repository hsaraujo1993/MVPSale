# README Frontend — Instruções e Checklist de QA

Este documento orienta como executar rapidamente o frontend em Django Templates e traz um checklist de QA pronto para uso.

## Pré-requisitos

- Python 3.10+ (venv recomendado)
- Dependências Django instaladas (no virtualenv do projeto)
- A API backend deve estar disponível (o gerenciador `manage.py` do projeto está em `backend/manage.py`)

## Como rodar (modo rápido)

Abra um terminal (cmd.exe) na raiz do repositório e execute:

```cmd
python backend\manage.py runserver
```

Isso inicia o servidor Django (por padrão em `http://127.0.0.1:8000/`).

Se precisar migrar o banco ou criar um superusuário (uma vez):

```cmd
python backend\manage.py migrate
python backend\manage.py createsuperuser
```

Credenciais mock para testes manuais (se houver autenticação mock implementada):

- user: `admin`
- password: `admin`

> Observação: o projeto pode usar autenticação por sessão; use o formulário de login padrão (templates/auth/login.html) ou a rota de login já implementada.

## Arquivos e localizações importantes

- `backend/README.md` — especificação geral (este arquivo está vinculado a ele).
- `backend/README_frontend.md` — este guia com o checklist de QA.
- Templates sugeridos: `templates/` (estruturas e partials listadas no `backend/README.md`).
- Helpers JS (sugeridos): `static/js/http.js`, `static/js/csrf.js`, `static/js/ui.js`.

## Teste rápido (smoke)

- Acesse `http://127.0.0.1:8000/` no navegador e verifique se a página de login ou dashboard carrega.
- Faça login com credenciais mock e verifique navegação básica (Dashboard, Catálogo, Pedidos).
- Teste upload de um arquivo `.xml` na tela de Notas de Fornecedores e valide o preview de metadados.

## Checklist de QA (pronto para uso)

Execute estes passos manualmente ou transforme-os em testes e2e (Playwright / Cypress):

1. Login
   - [ ] A página de login carrega sem erros de JS.
   - [ ] Login com credenciais mock efetua redirecionamento para o dashboard.
   - [ ] Sessão é preservada ao navegar entre páginas.

2. Navegação e layout
   - [ ] Navbar e sidebar aparecem em resoluções mobile e desktop.
   - [ ] Dark mode ativado por padrão; toggle para light funciona.
   - [ ] Sem overflow indesejado em 320px / 768px / 1024px / 1440px.

3. Listagens (para cada recurso)
   - [ ] Lista carrega dados da API (`/api/<recurso>/?page=&search=&ordering=`).
   - [ ] Paginação funciona e atualiza a tabela.
   - [ ] Busca e ordenação retornam resultados esperados.
   - [ ] Ações (ver/editar/excluir) estão funcionando e com confirmação quando necessário.

4. Formulários
   - [ ] Criação e edição (`form.html`) validam campos obrigatórios antes do envio.
   - [ ] Erros retornados pelo DRF aparecem associados ao campo correto.
   - [ ] Submissão bem-sucedida mostra toast de sucesso e atualiza a lista.

5. Upload XML (Notas de Fornecedores)
   - [ ] Aceita apenas arquivos `.xml` (input file type + validação cliente).
   - [ ] Após upload, preview dos metadados é exibido conforme retorno da API.
   - [ ] Em erro de parse, alert padronizado mostra mensagem e detalhes (quando disponíveis).

6. Caixa
   - [ ] Tela mostra status atual (aberto/fechado) e operador.
   - [ ] Abrir/Fechar caixa envia `POST` e atualiza status/horário corretamente.
   - [ ] Movimentos do dia aparecem e somatórios batem com entradas/saídas.

7. Dashboard
   - [ ] KPIs carregam (pedidos do dia, faturamento, tíquete médio, estoque crítico).
   - [ ] Lista de eventos de auditoria atualiza e exibe metadados.
   - [ ] Gráfico em `<canvas>` plota dados e lida com ausência de dados sem quebrar.

8. Acessibilidade
   - [ ] Labels estão associados aos inputs.
   - [ ] Modais gerenciam foco (foco inicial e retorno ao fechar).
   - [ ] Contraste no dark mode atende mínimos aceitáveis (fácil leitura).

9. Erros e UX
   - [ ] Toasts/uniformidade de alertas (sucesso/erro) estão padronizados.
   - [ ] Nenhum erro JS crítico no console durante fluxos principais.

10. Performance e responsividade
    - [ ] Tempo de resposta razoável ao carregar listas (paginação ativa).
    - [ ] Tabelas grandes usam scroll com cabeçalho sticky quando necessário.

## Automação (opcional)

Sugestão de estrutura de teste e2e com Playwright:

- `tests/e2e/login.spec.ts` — testa fluxo de login e navegação.
- `tests/e2e/catalog.spec.ts` — lista, busca, paginação, CRUD.
- `tests/e2e/nfe_upload.spec.ts` — upload XML e verificação do preview.

Com Playwright instalado, exemplo rápido para rodar todos os testes:

```cmd
npx playwright test
```

## Observações finais

- Este arquivo é um guia prático; ajuste rotas/API caso o backend use endpoints diferentes.
- Se precisar, eu posso gerar skeletons dos templates e os helpers JS para acelerar a implementação.

---

*Gerado automaticamente por ferramenta; ajuste conforme necessidades do projeto.*

