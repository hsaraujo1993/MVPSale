# Política de Custos e Precificação

Este documento descreve a estratégia recomendada para lojas de varejo, implementada no MVPSale.

## Visão Geral

- Custo de estoque (contábil): custo médio ponderado (`Product.avg_cost_price`).
- Custo de reposição (precificação): último custo líquido de compra (`Product.last_cost_price`).
- Formação de preço: `sale_price = custo_base × (1 + margem/100)`.
  - Quando `margem = 0`, `sale_price = 0` (trava operacional).
  - Piso de margem mínima via `MIN_MARGIN_PERCENT` (global) em `settings`.

## Campos novos

Tabela `catalog_product` (model `Product`):
- `last_cost_price` (Decimal, 2 casas): último custo líquido de compra.
- `avg_cost_price` (Decimal, 2 casas): custo médio ponderado.

Tabela `purchase_supplierproduct` (model `SupplierProduct`):
- `last_cost` (Decimal, 2 casas): último custo do fornecedor para o produto.
- `last_purchase_date` (Date): data da última compra para o vínculo fornecedor–produto.

## Configuração

Em `backend/MVPSale/settings/base.py`:

- `PRICE_COST_BASIS` (env): base de custo para precificação. Valores:
  - `last` (padrão): usa `last_cost_price` se disponível; senão, `cost_price`.
  - `average`: usa `avg_cost_price` se disponível; senão, `cost_price`.
- `PRICE_ROUNDING` (env): estratégia de arredondamento de preços. Opções:
  - `none` (padrão): arredonda para 2 casas (HALF_UP).
  - `psychological`: aplica finais `.99` quando valor ≥ 1,00.
  - `step:<tamanho>`: arredonda para o próximo múltiplo do passo informado (ex.: `step:0.10`, `step:0.05`).

Exemplo `.env`:

```
PRICE_COST_BASIS=last
MIN_MARGIN_PERCENT=0
```

## Importação de NFe (Compras)

Durante a importação (`purchase/services/nfe_import.py`):

1. Faz o match/criação do `Product`.
2. Cria/atualiza `SupplierProduct` e agora também define:
   - `last_cost` com `vUnCom` do XML
   - `last_purchase_date` com a data de emissão
3. Aplica `StockMovement` do tipo `ENTRADA` para incrementar estoque.
4. Atualiza custos do `Product`:
   - `last_cost_price` = custo unitário (`vUnCom`)
   - `avg_cost_price` = média ponderada: `(custo_médio_atual × qty_atual + vUnCom × qty_entrada) ÷ (qty_atual + qty_entrada)`

Obs.: quando não há histórico, a média inicia em `vUnCom`.

## Cálculo de Preço

O `Product.save()` recalcula sempre o `sale_price` usando a base de custo configurada e aplicando o arredondamento:

1. Se `margem = 0`: `sale_price = 0`.
2. Senão: usa custo baseado em `PRICE_COST_BASIS` (last/average, com fallback `cost_price`) e aplica `PRICE_ROUNDING`.

Há também um comando de manutenção para recomputar preços em massa:

```
python backend/manage.py recalc_sale_prices --all
```

Este comando considera `PRICE_COST_BASIS` e aplica arredondamento a 2 casas.

## API

- O `ProductSerializer` expõe adicionalmente (via representação):
  - `last_cost_price`, `avg_cost_price`, `pricing_cost` (custo efetivo usado) e `suggested_sale_price` (preço sugerido com arredondamento).
- O endpoint de importação de NFe e de estoque permanecem os mesmos; os novos campos são refletidos automaticamente nos objetos retornados.

## Boas Práticas Operacionais

- Ao importar NFe com aumento relevante de custo, revisar margem/preço.
- Considerar fila de “itens para revisar” no front quando `last_cost_price` variar acima de X%.
- Definir política de arredondamento (ex.: finais `.99` ou passos de R$ 0,10) conforme o segmento.

## Revisão de Preço (endpoint)

Endpoint para identificar itens que precisam de revisão de preço com base na variação de custo e no desvio entre preço atual e preço sugerido.

- Rota: `GET /api/v1/catalog/products/price-review/`
- Parâmetros (query):
  - `threshold` (opcional): limite percentual, ex.: `0.05` para 5%. Default: `PRICE_REVIEW_THRESHOLD` (5%).
  - `limit` (opcional): máximo de itens retornados. Default: 100.
- Critérios de alerta (flag):
  - `|suggested - sale_price| / sale_price >= threshold`, ou
  - `|last_cost_price - avg_cost_price| / avg_cost_price >= threshold` (quando ambos existem)
- Resposta (exemplo):
```
{
  "count": 2,
  "threshold": 0.05,
  "items": [
    {
      "id": 12,
      "uuid": "...",
      "name": "Fone de Ouvido",
      "sku": "P000012",
      "margin": "25.00",
      "sale_price": "125.00",
      "suggested_sale_price": "139.99",
      "pricing_cost": "112.00",
      "last_cost_price": "112.00",
      "avg_cost_price": "100.00",
      "price_diff_pct": 0.1192,
      "cost_diff_pct": 0.12,
      "basis": "last"
    }
  ]
}
```

Configuração relacionada:

- `PRICE_REVIEW_THRESHOLD` (env): default `0.05` (5%).
