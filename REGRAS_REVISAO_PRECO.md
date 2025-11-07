# Revisão de Preço — Regras (simples e claras)

Este documento descreve, de forma direta, como a tela de Revisão de Preço funciona e quando um produto aparece nela.

## O que a tela mostra
- Produto e SKU
- Custo (base)
- Margem (%)
- Preço atual
- Preço sugerido
- Δ Preço (%): diferença entre sugerido e atual
- Δ Custo (%): diferença entre último custo e custo médio

## Como cada valor é calculado
- Custo (base): definido por configuração `PRICE_COST_BASIS`:
  - `last` (padrão): usa `last_cost_price` (última compra)
  - `average`: usa `avg_cost_price` (custo médio ponderado)
  - fallback: `cost_price` do produto
- Preço sugerido: `custo_base × (1 + margem/100)` com arredondamento opcional (`PRICE_ROUNDING`)
- Δ Preço: `(preço_sugerido − preço_atual) / preço_atual`
- Δ Custo: `(last_cost_price − avg_cost_price) / avg_cost_price`

## Quando o produto aparece na lista
O item é incluído se QUALQUER condição abaixo for verdadeira:
1. `abs(Δ Preço) ≥ PRICE_REVIEW_THRESHOLD` (padrão: 0,05 = 5%)
2. `abs(Δ Custo) ≥ PRICE_REVIEW_THRESHOLD`
3. `needs_review == True` (marcado manualmente ou por serviço)
4. `sale_price == 0` OU `margin == 0`

Observação: se preço e margem estiverem consistentes com o custo (base), é esperado `Δ Preço = 0%`. O item ainda pode aparecer por regras 2–4.

## Ações na tela
- Marcar revisado: define `needs_review = False` e atualiza a lista
- Marcar pendente: define `needs_review = True` e atualiza a lista

## Filtros disponíveis
- Paginação: `page`, `page_size`
- Busca: `search` (por nome/SKU)
- Ordenação: `ordering` (ex.: `-price_diff_pct`, `price_diff_pct`, `-cost_diff_pct`, `name`, `sku`)

## Configurações relacionadas
- Arquivo: `backend/MVPSale/settings/base.py`
  - `PRICE_COST_BASIS`: `last` ou `average` (define a base do custo)
  - `PRICE_ROUNDING`: estratégia de arredondamento (ex.: `none`)
  - `PRICE_REVIEW_THRESHOLD`: limiar de variação (ex.: `0.05` para 5%)

Você pode ajustar essas variáveis via ambiente (ENV) para testes, se necessário.

## Evidências rápidas (como testar)
1. Rodar o seed de demonstração:
   - Windows: `.\.venv\Scripts\python.exe backend\manage.py seed_price_review_demo`
   - Linux/macOS: `./.venv/bin/python backend/manage.py seed_price_review_demo`
2. Abrir a tela: `http://127.0.0.1:8000/price-review` e buscar por `DEMO-`
   - `DEMO-PRICE`: mostra Δ Preço > 0% (preço atual propositalmente diferente do sugerido) e Δ Custo > 0%
   - `DEMO-COST`: Δ Custo > 0% (last ≠ average) e Δ Preço = 0%
   - `DEMO-MANUAL`: incluído por margem/preço zero ou `needs_review=True`

## Endpoints
- Página: `/price-review` → `backend/MVPSale/urls.py`
- API: `GET /api/v1/catalog/products/price-review/`
  - Retorno no padrão DRF: `count`, `next`, `previous`, `results[]`, `threshold`

