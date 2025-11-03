---
name: Sistema de Vendas Completo
type: sprint_flow
version: 1.5
owner: Henrique
priority: high
current_sprint: 8
project:
  django_project_name: MVPSale          # pacote do projeto atual
  alt_recommendation: mvpstore          # sugestÃ£o PEP8 (opcional)
api:
  base_url: /api
  versioning: url
  current_version: v1
docs:
  tool: drf-spectacular
  swagger_url: /api/schema/swagger/
  redoc_url: /api/schema/redoc/
security:
  auth: JWT (SimpleJWT)
  roles:
    - total
    - leitura
    - desconto
    - fechamento
business_rules:
  cashier_required_for_sale: true                # Ã© obrigatÃ³rio abrir caixa para finalizar venda
  nfe_cancel_reverts_stock: true                 # cancelar NF-e/pedido reverte estoque
  product_can_have_multiple_suppliers: true      # mesmo produto pode ter vÃ¡rios fornecedores
  stock_min_max_alerts: true                     # alertas no dashboard
  block_sale_if_zero_stock: true                 # proÃ­be venda se estoque zerado
  prevent_negative_stock: true                   # nÃ£o permitir estoque negativo
  seller_discount_limit_per_user: true           # cada vendedor tem seu prÃ³prio teto de desconto
  price_floor_by_margin: true                    # nÃ£o permitir preÃ§o abaixo do custo + margem mÃ­nima configurÃ¡vel
  promotion_stack_mode: single_best               # aplicar apenas a melhor promoÃ§Ã£o vigente
  loyalty_points_optional: false                 # (pode ser ativado futuramente)
  cart_inventory_reservation:
    enabled: true
    ttl_minutes: 15                               # reserva de estoque no carrinho por 15min
  returns_policy:
    allow_cancellation_before_invoice: true
    allow_return_after_invoice: true
    return_reverts_stock_and_creates_credit_note: true
  audit_trail:
    order_state_changes: true
    price_override_reason_required: true
  rounding:
    monetary_precision: 2
    rounding_mode: HALF_UP
  units_and_conversions:
    enforce_base_unit: true
    allow_unit_conversion_on_purchase: true
  barcode_policy:
    accept_sem_gtin: true                         # aceitar 'SEM GTIN'
    fallback_from_supplier_code_when_missing: true
  supplier_product_mandatory_fiscal_fields:       # exigido para emitir NF-e de venda
    - NCM
    - CEST
    - CFOP
    - ICMS.CST/orig
    - IPI.cEnq/CST
    - PIS.CST/aliquota
    - COFINS.CST/aliquota
    - uCom/uTrib
    - cEAN/cEANTrib
execution:
  commands:
    start: "Execute a Sprint <nÃºmero>"
    approve: "Aprovo a Sprint <nÃºmero> â€” marque como concluÃ­da"
    next: "Execute a prÃ³xima sprint"
    status: "Mostrar status das sprints"
  policy:
    one_sprint_at_a_time: true
    manual_validation_required: true
    on_approval:
      - update_yaml_status_to_completed: true
      - append_log_entry: true
      - increment_current_sprint: true
sprints:
  - id: 1
    name: Estrutura do Projeto e Base do Backend
    status: completed
  - id: 2
    name: App Catalog
    status: completed
  - id: 3
    name: App People
    status: completed
  - id: 4
    name: App Stock
    status: completed
  - id: 5
    name: App Purchase
    status: completed
  - id: 6
    name: App Sale
    status: completed
  - id: 7
    name: App Payment
    status: completed
  - id: 8
    name: App NFe
    status: in_progress
  - id: 9
    name: App Cashier
    status: pending
  - id: 10
    name: Frontend (HTML + Tailwind + JS)
    status: pending
  - id: 11
    name: IntegraÃ§Ã£o, Testes e Deploy
    status: pending
---

# ðŸ§­ FLUXO DE SPRINTS â€” SISTEMA COMPLETO DE VENDAS

O agente executa **uma sprint por vez**, aguarda **validaÃ§Ã£o manual** e, quando aprovado, **marca como concluÃ­da** e avanÃ§a `current_sprint`.

---

## ðŸ“š MODELOS, ENDPOINTS E REGRAS DE NEGÃ“CIO (BASE OFICIAL)

### 1) Catalog (CatÃ¡logo)
**Modelos**
- **Category**: `id`, `nome`, `slug (auto)`, `ativa`
- **Brand**: `id`, `nome`, `ativa`
- **Product**:
  - `sku` (auto), `nome`, `descricao`, `categoria`, `marca`
  - `preco_custo`, `margem`, `preco_venda` (calculado)
  - `barcode`, `ativo`, `criado_em`, `atualizado_em`
  - `calcular_preco_venda() = custo + (custo * margem/100)`
- **Promotion**: `produto`, `percentual_desconto`, `data_inicio`, `data_fim`, `ativa`

**Endpoints v1**
- `GET /api/v1/catalog/products/?search=&brand=&category=&ordering=`
- `POST /api/v1/catalog/products/`
- `GET/POST /api/v1/catalog/categories/`
- `GET/POST /api/v1/catalog/brands/`
- `GET/POST /api/v1/catalog/promotions/`

---

### 2) People (Pessoas)
**Modelos**
- **Customer**: `nome`, `cpf_cnpj`, `email`, `telefone`, `endereco`, `cep`, `cidade`, `uf`
- **Supplier**: `razao_social`, `cnpj`, `email`, `telefone`, `endereco`, `cep`, `cidade`, `uf`
- **Seller**: `usuario`, `nome`, `nivel_acesso (total|leitura|desconto|fechamento)`, `desconto_maximo` *(percentual, por usuÃ¡rio)*

**Regras**
- **Desconto por vendedor**: cada vendedor tem **margem mÃ¡xima individual** (`desconto_maximo`).  
  Ex.: *vendedor X* â†’ **10%**. Backend deve **validar e bloquear** descontos acima da margem; frontend deve **limitar input**.

**Endpoints v1**
- `GET/POST /api/v1/people/customers/`
- `GET/POST /api/v1/people/suppliers/`
- `GET/POST /api/v1/people/sellers/`

---

### 3) Stock (Estoque)
**Modelos**
- **Stock**: `produto`, `quantidade_atual`, `minima`, `maxima`, `status: ZERADO|ABAIXO|OK|ACIMA`
- **StockMovement**: `produto`, `tipo: ENTRADA|SAIDA|AJUSTE`, `quantidade`, `referencia (pedido|nota|ajuste_id)`, `observacao`, timestamps

**Regras**
- **AtualizaÃ§Ã£o automÃ¡tica de status**: `ZERADO`, `ABAIXO`, `OK`, `ACIMA`.
- **Bloquear venda** se `ZERADO` e **nÃ£o permitir negativo**.
- Dashboard exibe **alertas** de mÃ­nimo/mÃ¡ximo.
- **Reserva de estoque** no carrinho por 15min.

**Endpoints v1**
- `GET /api/v1/stock/`
- `GET/POST /api/v1/stock/movements/`

---

### 4) Purchase (Compras) â€” **ImportaÃ§Ã£o XML e Dados Fiscais**
**Modelos**
- **SupplierProduct**:  
  `fornecedor`, `produto`, `codigo_fornecedor` (= cProd), `codigo_universal` (quando houver), `barcode`,  
  **fiscais**: `ncm`, `cfop`, `cest`, `cst_icms`, `origem_icms`, `ipi_cenq`, `ipi_cst`, `pis_cst`, `pis_aliq`, `cofins_cst`, `cofins_aliq`,  
  **unidades**: `uCom`, `uTrib`.  
  Criado/atualizado ao **importar XML** da nota fiscal.
- **PurchaseInvoice**: `numero`, `serie`, `fornecedor`, `data_emissao`, `valor_total`, `arquivo_xml`, `arquivo_pdf`
- **PurchaseInstallment**: `nota_fiscal`, `numero_parcela`, `data_vencimento`, `valor`, `status: PENDENTE|PAGO|ATRASADO`

**Regras**
- Ao **importar XML de compra**:
  - Se produto nÃ£o existir, **criar** `Product` e **acrescentar estoque** (movimento de **ENTRADA**).
  - **Popular `SupplierProduct`** com **cÃ³digos e dados tributÃ¡rios obrigatÃ³rios** (abaixo).
  - **Gerar parcelas** `PurchaseInstallment`.
  - Marcar parcelas vencidas como **ATRASADO** por job diÃ¡rio.

**Mapeamento do XML (NFe 4.00) para `SupplierProduct` e venda**
> Fonte: XML anexado pelo usuÃ¡rio (exemplo real). :contentReference[oaicite:0]{index=0}

- **Item**: `/nfeProc/NFe/infNFe/det[]`
- **CÃ³digos & DescriÃ§Ã£o**  
  - `codigo_fornecedor` â† `det/prod/cProd`  
  - `descricao` â† `det/prod/xProd`  
  - `barcode` â† **preferÃªncia**: `det/prod/cEAN` (ou `cEANTrib`); se for `"SEM GTIN"`, extrair do texto em `det/infAdProd` quando presente (`COD. BARRAS: XXXXX`).  
- **Fiscais (para venda/NFe)**  
  - `ncm` â† `det/prod/NCM`  
  - `cest` â† `det/prod/CEST` (quando existir)  
  - `cfop` â† `det/prod/CFOP`  
  - `uCom` â† `det/prod/uCom` ; `uTrib` â† `det/prod/uTrib`  
  - **ICMS** (ex.: `ICMS60` no XML de exemplo):  
    - `origem_icms` â† `det/imposto/ICMS/*/orig`  
    - `cst_icms` â† `det/imposto/ICMS/*/CST`  
  - **IPI**:  
    - `ipi_cenq` â† `det/imposto/IPI/cEnq`  
    - `ipi_cst` â† `det/imposto/IPI/*/CST` (pode ser `IPINT` no exemplo)  
  - **PIS/COFINS** (alÃ­quota quando houver):  
    - `pis_cst` â† `det/imposto/PIS/*/CST`  
    - `pis_aliq` â† `det/imposto/PIS/PISAliq/pPIS` *(quando existir)*  
    - `cofins_cst` â† `det/imposto/COFINS/*/CST`  
    - `cofins_aliq` â† `det/imposto/COFINS/COFINSAliq/pCOFINS` *(quando existir)*  
- **ObservaÃ§Ãµes Ãºteis do exemplo**  
  - VÃ¡rios itens vÃªm com `cEAN`/`cEANTrib = "SEM GTIN"` e **informam o cÃ³digo de barras** em `infAdProd` no formato  
    â€œ`COD. BARRAS: 605110 - LOTE: ...`â€, **usar esse valor como `barcode`** quando `cEAN` for invÃ¡lido.  
  - Exemplo de dados tributÃ¡rios encontrados: **ICMS60 (CST=60)**, **IPI IPINT (CST=53)**, **PIS/COFINS CST=01** com alÃ­quotas informadas em alguns itens.  
- **Outros campos relevantes**  
  - Quantidades/valores: `qCom`, `vUnCom`, `vProd` (armazenar como referÃªncia de custo/Ãºltimo preÃ§o de compra).  
  - `indTot` para composiÃ§Ã£o do total da NF.  

**Endpoints v1**
- `POST /api/v1/purchase/invoices/import_xml/` (multipart `arquivo_xml`)  
- `GET/POST /api/v1/purchase/invoices/`  
- `GET/POST /api/v1/purchase/installments/`

---

### 5) Sale (Vendas)
**Modelos**
- **Cart**: `cliente`, `vendedor`, `tipo: ORCAMENTO|PEDIDO`, `ativo`, `subtotal`, `desconto`, `total`
- **Order**: `cliente`, `vendedor`, `status: RASCUNHO|ABERTO|FATURADO|CANCELADO`, `total`, `forma_pagamento`, `condicao_pagamento`, `desconto_aplicado`
- **OrderItem**: `pedido`, `produto`, `quantidade`, `preco_unitario`, `subtotal`

**Regras**
- **ObrigatÃ³rio abrir Caixa** para **checkout** (`Cart â†’ Order`).  
- **Baixa de estoque** em **SAÃDA** no faturamento; **estorno** (ENTRADA) no cancelamento/NF-e cancelada.  
- **Quantidade do item â‰¤ estoque disponÃ­vel** (respeitando reserva do carrinho).  
- **Desconto** nÃ£o pode ultrapassar o **teto do vendedor** (`Seller.desconto_maximo`).

**Endpoints v1**
- `POST /api/v1/cart/`
- `POST /api/v1/cart/{id}/items/`
- `POST /api/v1/cart/{id}/checkout/` (requer **Caixa aberto**)
- `GET/POST /api/v1/order/`
- `POST /api/v1/order/{id}/cancel/`

---

### 6) Payment (Pagamentos)
**Modelos**
- **PaymentMethod**: `PIX|CARTAO|DINHEIRO|BOLETO`
- **PaymentCondition**: `nome`, `quantidade_parcelas`, `entrada?`, `dias_entre_parcelas`, `juros_aa?` ou `juros_am?`
- **CreditCardFee**: `bandeira`, `parcelas`, `taxa (%)`

**Regras**
- Aplicar **juros/taxas** ao total do pedido conforme mÃ©todo/condiÃ§Ã£o.  
- **SimulaÃ§Ã£o de parcelas** retorna JSON detalhando valores, datas e totais.

**Endpoints v1**
- `GET/POST /api/v1/payment/methods/`
- `GET/POST /api/v1/payment/conditions/`
- `GET/POST /api/v1/payment/fees/`
- `POST /api/v1/payment/simulate/`

---

### 7) NFe (Notas Fiscais de Venda)
**Modelos**
- **NFeSale**: `pedido`, `chave_acesso`, `numero`, `serie`, `status: EMITIDA|CANCELADA|ERRO`, `mensagem_status`

**Regras**
- IntegraÃ§Ã£o com **Focus NFe**: **emitir**, **consultar**, **cancelar**, **download** XML/PDF.  
- **Cancelar NF-e** â†’ **reverter estoque** e `Order=CANCELADO`.

**Endpoints v1**
- `POST /api/v1/nfe/{order_id}/emitir/`
- `POST /api/v1/nfe/{id}/cancelar/`
- `GET /api/v1/nfe/{id}/xml/`
- `GET /api/v1/nfe/{id}/pdf/`

---

### 8) Cashier (Caixa)
**Modelos**
- **Cashier**: `vendedor`, `data_abertura`, `data_fechamento`, `status: ABERTO|FECHADO`, `saldo_inicial`, `saldo_final`

**Regras**
- **ObrigatÃ³rio** caixa **ABERTO** para finalizar vendas.  
- Fechamento calcula `saldo_final` e relaciona vendas/recebimentos ao caixa.

**Endpoints v1**
- `POST /api/v1/cashier/open/`
- `POST /api/v1/cashier/close/`
- `GET /api/v1/cashier/current/`

---

## âœ… DEFINITION OF DONE (geral)
- Regras de negÃ³cio acima **implementadas e validadas**.  
- **ValidaÃ§Ãµes de desconto por vendedor** no backend e limites no frontend.  
- **Bloqueios**: sem caixa aberto, estoque zerado/negativo, preÃ§o abaixo do piso.  
- OpenAPI/Swagger atualizados; mensagens de erro claras.

---

# ðŸ“… SPRINTS (sequÃªncia oficial)

## ðŸ SPRINT 1 â€” Estrutura do Projeto e Base do Backend
**Status:** â³ Em andamento  
**Objetivo:** Esqueleto do backend e documentaÃ§Ã£o base.  
**Entregas:** projeto (MVPSale), apps registradas, JWT, versionamento `/api/v1/*`, docs, healthcheck.

---

## ðŸ§© SPRINT 2 â€” App Catalog
**Objetivo:** CRUD de categorias, marcas, produtos e promoÃ§Ãµes.  
**Regras-chave:** `calcular_preco_venda`, promoÃ§Ã£o â€œmelhor preÃ§oâ€.  
**CritÃ©rios:** filtros, busca e ordering.

---

## ðŸ‘¥ SPRINT 3 â€” App People
**Objetivo:** Clientes, Fornecedores, Vendedores com **desconto_maximo** por usuÃ¡rio.  
**CritÃ©rios:** validaÃ§Ãµes CPF/CNPJ; polÃ­ticas por `nivel_acesso`.

---

## ðŸ“¦ SPRINT 4 â€” App Stock
**Objetivo:** Estoque e MovimentaÃ§Ãµes; reservas no carrinho.  
**CritÃ©rios:** bloquear venda com `ZERADO`, sem negativo, baixa/estorno corretos.

---

## ðŸ§¾ SPRINT 5 â€” Purchase (XML + Fiscais)
**Objetivo:** Importar XML, criar/atualizar `SupplierProduct` (cÃ³digos e **dados fiscais obrigatÃ³rios**), gerar parcelas e entrada de estoque.  
**CritÃ©rios:** XML de exemplo preenche NCM/CEST/CFOP/CST/â€¦ e **barcode** (via cEAN/cEANTrib ou `infAdProd`).

---

## ðŸ›’ SPRINT 6 â€” Sale
**Objetivo:** Carrinho â†’ Pedido; validaÃ§Ãµes de estoque e desconto por vendedor.  
**CritÃ©rios:** fluxo completo e mensagens de erro adequadas.

---

## ðŸ’³ SPRINT 7 â€” Payment
**Objetivo:** MÃ©todos/CondiÃ§Ãµes/Taxas; **simulaÃ§Ã£o de parcelas**.  
**CritÃ©rios:** aplicaÃ§Ã£o correta no total do pedido.

---

## ðŸ§¾ SPRINT 8 â€” NFe
**Objetivo:** EmissÃ£o/Consulta/Cancelamento; download XML/PDF.  
**CritÃ©rios:** cancelamento reverte estoque e status do pedido.

---

## ðŸ’° SPRINT 9 â€” Cashier
**Objetivo:** Abertura/fechamento; associaÃ§Ã£o de vendas ao caixa.  
**CritÃ©rios:** bloqueio de checkout sem caixa aberto.

---

## ðŸ–¥ï¸ SPRINT 10 â€” Frontend
**Objetivo:** PÃ¡ginas e componentes; consumo da API; UX responsiva.  
**CritÃ©rios:** fluxos principais navegÃ¡veis.

---

## ðŸš€ SPRINT 11 â€” IntegraÃ§Ã£o, Testes e Deploy
**Objetivo:** Amarrar tudo, testes E2E, preparaÃ§Ã£o de produÃ§Ã£o.  
**CritÃ©rios:** compraâ†’vendaâ†’NF-eâ†’caixa Ã­ntegros; documentaÃ§Ã£o atualizada.

---

## âš™ï¸ EXECUÃ‡ÃƒO (COMANDOS AO AGENTE)
- **Iniciar**: `Execute a Sprint 1`  
- **Aprovar e finalizar**: `Aprovo a Sprint <nÃºmero> â€” marque como concluÃ­da`  
- **PrÃ³xima**: `Execute a prÃ³xima sprint`  
- **Status**: `Mostrar status das sprints`

---

## ðŸ§· LOG (o agente anexa automaticamente)
<!--
- 2025-10-28 10:33 BRT â€” Sprint 1 iniciada
- 2025-10-28 15:10 BRT â€” Sprint 1 concluÃ­da; validado por Henrique
- 2025-10-29 09:05 BRT â€” Sprint 2 iniciada
-->


---

## Checklist Operacional Pós-Importação (Purchase)
- Recalcular preço de venda (garantir regra margem=0 => sale_price=0):
  - python backend/manage.py recalc_sale_prices 
- Opcional (forçar todos conforme custo + margem):
  - python backend/manage.py recalc_sale_prices --all 
- Validação rápida:
  - Produtos com margin=0 devem estar com sale_price=0.
  - Conferir entradas de estoque em /stock.
