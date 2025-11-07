from __future__ import annotations

import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List
import logging

import xmltodict
from django.db import transaction

from catalog.models import Category, Brand, Product
from people.models import Supplier
from stock.models import StockMovement
from ..models import PurchaseInvoice, PurchaseInstallment, SupplierProduct
from django.conf import settings as s
from core.pricing import apply_rounding

log = logging.getLogger(__name__)


def _ensure_default_catalog() -> tuple[Category, Brand]:
    cat, _ = Category.objects.get_or_create(name="Geral")
    brand, _ = Brand.objects.get_or_create(name="Genérica")
    return cat, brand


def _as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


@transaction.atomic
def import_nfe_xml(xml_text: str) -> Dict[str, Any]:
    log.info("[nfe_import] start parse")
    doc = xmltodict.parse(xml_text)
    nfe = (
        doc.get("nfeProc", {}).get("NFe")
        or doc.get("NFe")
    )
    if not nfe:
        raise ValueError("XML NFe inválido")

    inf = nfe["infNFe"] if "infNFe" in nfe else nfe
    ide = inf.get("ide", {})
    emit = inf.get("emit", {})
    det_list = _as_list(inf.get("det"))
    cobr = inf.get("cobr", {})
    dup_list = _as_list(cobr.get("dup"))
    total = inf.get("total", {}).get("ICMSTot", {})

    # Supplier
    supplier_cnpj = (emit.get("CNPJ") or emit.get("CPF") or "").strip()
    supplier_name = (emit.get("xNome") or "Fornecedor").strip()
    supplier, sup_created = Supplier.objects.get_or_create(
        cnpj="".join(ch for ch in supplier_cnpj if ch.isdigit()).zfill(14)[:14],
        defaults={"corporate_name": supplier_name},
    )
    log.info("[nfe_import] supplier %s (created=%s)", supplier.id, sup_created)

    # Invoice
    number = ide.get("nNF") or "0"
    series = str(ide.get("serie") or "")
    issue_raw = ide.get("dhEmi") or ide.get("dEmi")
    if issue_raw:
        try:
            issue_date = datetime.date.fromisoformat(issue_raw[:10])
        except Exception:
            issue_date = None
    else:
        issue_date = None
    vNF = Decimal(str(total.get("vNF") or "0"))

    # Prevent duplicates
    existing = PurchaseInvoice.objects.filter(supplier=supplier, number=str(number), series=series).first()
    if existing:
        log.warning("[nfe_import] duplicate invoice supplier=%s number=%s series=%s", supplier.id, number, series)
        raise ValueError("Nota fiscal já importada para este fornecedor (número/série).")

    inv = PurchaseInvoice.objects.create(
        number=str(number),
        series=series,
        supplier=supplier,
        issue_date=issue_date,
        total_value=vNF,
        xml=xml_text,
    )
    log.info("[nfe_import] invoice created id=%s number=%s series=%s total=%s", inv.id, number, series, vNF)

    # Catalog defaults
    cat, brand = _ensure_default_catalog()

    # Items
    created_products: List[int] = []
    for det in det_list:
        prod = det.get("prod", {})
        imposto = det.get("imposto", {})
        q_raw = Decimal(str(prod.get("qCom") or "0"))
        # Normalize quantity to 3 decimal places to satisfy StockMovement constraint
        qCom = q_raw.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        cProd = str(prod.get("cProd") or "").strip()
        xProd = str(prod.get("xProd") or "Produto").strip()
        barcode = str(prod.get("cEAN") or "").strip()
        ncm = str(prod.get("NCM") or "").strip()
        cfop = str(prod.get("CFOP") or "").strip()
        cest = str(prod.get("CEST") or "").strip()
        uCom = str(prod.get("uCom") or "UN").strip()
        uTrib = str(prod.get("uTrib") or uCom).strip()

        # Taxes
        icms = imposto.get("ICMS", {})
        # ICMS can be nested like ICMS -> ICMS00 -> orig, CST
        if isinstance(icms, dict) and len(icms) == 1:
            icms = list(icms.values())[0]
        icms_origem = str(icms.get("orig") or "").strip()
        icms_cst = str(icms.get("CST") or icms.get("CSOSN") or "").strip()

        ipi = imposto.get("IPI", {})
        if isinstance(ipi, dict) and len(ipi) == 1 and isinstance(list(ipi.values())[0], dict):
            # e.g. IPI -> IPITrib or IPINT
            ipi_data = list(ipi.values())[0]
        else:
            ipi_data = ipi or {}
        ipi_cenq = str(ipi.get("cEnq") or ipi_data.get("cEnq") or "").strip()
        ipi_cst = str(ipi_data.get("CST") or "").strip()

        pis = imposto.get("PIS", {})
        if isinstance(pis, dict) and len(pis) == 1:
            pis = list(pis.values())[0]
        pis_cst = str(pis.get("CST") or "").strip()
        pis_aliq = Decimal(str(pis.get("pPIS") or 0))

        cofins = imposto.get("COFINS", {})
        if isinstance(cofins, dict) and len(cofins) == 1:
            cofins = list(cofins.values())[0]
        cofins_cst = str(cofins.get("CST") or "").strip()
        cofins_aliq = Decimal(str(cofins.get("pCOFINS") or 0))

        # Product: avoid duplicates. Try matches in this order:
        # 1) barcode
        # 2) SupplierProduct by (supplier, supplier_code)
        # 3) Product by exact name (case-insensitive)
        product = None
        if barcode:
            product = Product.objects.filter(barcode=barcode).first()
        if product is None and cProd:
            sp_match = SupplierProduct.objects.select_related("product").filter(supplier=supplier, supplier_code=cProd).first()
            if sp_match and sp_match.product_id:
                product = sp_match.product
        if product is None:
            product = Product.objects.filter(name__iexact=xProd).first()
        if product is None:
            product = Product.objects.create(
                name=xProd,
                description="",
                category=cat,
                brand=brand,
                cost_price=Decimal(str(prod.get("vUnCom") or 0)),
                margin=Decimal("0"),
                barcode=barcode or "",
            )
            created_products.append(product.id)
            log.info("[nfe_import] product created id=%s name=%s barcode=%s", product.id, xProd, barcode)
        else:
            log.info("[nfe_import] product matched id=%s (barcode=%s, cProd=%s)", product.id, barcode, cProd)

        # SupplierProduct map
        sp, sp_created = SupplierProduct.objects.update_or_create(
            supplier=supplier,
            product=product,
            defaults={
                "supplier_code": cProd,
                "universal_code": str(prod.get("cEANTrib") or ""),
                "barcode": barcode,
                "ncm": ncm,
                "cfop": cfop,
                "cest": cest,
                "icms_cst": icms_cst,
                "icms_origem": icms_origem,
                "ipi_cenq": ipi_cenq,
                "ipi_cst": ipi_cst,
                "pis_cst": pis_cst,
                "pis_aliq": pis_aliq,
                "cofins_cst": cofins_cst,
                "cofins_aliq": cofins_aliq,
                "uCom": uCom,
                "uTrib": uTrib,
                "last_cost": Decimal(str(prod.get("vUnCom") or 0)),
                "last_purchase_date": issue_date or datetime.date.today(),
            },
        )
        log.info("[nfe_import] supplier_product %s (created=%s)", sp.id, sp_created)

        # Stock movement ENTRADA
        if qCom and qCom > 0:
            StockMovement.objects.create(product=product, type="ENTRADA", quantity=qCom, reference=f"NF {number}")
            log.info("[nfe_import] stock entry product=%s qty=%s", product.id, qCom)
        # Atualizar custos do produto (last e average)
        try:
            unit_cost = Decimal(str(prod.get("vUnCom") or 0))
            product.last_cost_price = unit_cost
            # calcular média ponderada usando estoque atual antes desta entrada
            from stock.models import Stock
            cur_qty = Decimal("0")
            try:
                st = Stock.objects.get(product=product)
                cur_qty = st.quantity_current or Decimal("0")
            except Stock.DoesNotExist:
                cur_qty = Decimal("0")
            total_qty = (cur_qty or Decimal("0")) + (qCom or Decimal("0"))
            if total_qty > 0:
                # usa avg anterior se houver, senão cost_price
                cur_avg = Decimal(str(product.avg_cost_price or product.cost_price or unit_cost))
                new_avg = ((cur_avg * cur_qty) + (unit_cost * qCom)) / total_qty
                # duas casas decimais
                product.avg_cost_price = new_avg.quantize(Decimal("0.01"))
            else:
                product.avg_cost_price = unit_cost.quantize(Decimal("0.01"))
            # Sinalizar revisão de preço conforme threshold ou condições operacionais
            try:
                threshold = Decimal(str(getattr(s, "PRICE_REVIEW_THRESHOLD", 0.05)))
                basis = getattr(s, "PRICE_COST_BASIS", "last")
                pricing_cost = unit_cost if basis == "last" else (product.avg_cost_price or unit_cost)
                margin = Decimal(str(product.margin or 0))
                if margin == 0:
                    suggested = Decimal("0.00")
                else:
                    base = pricing_cost + (pricing_cost * (margin / Decimal("100")))
                    suggested = apply_rounding(base, getattr(s, "PRICE_ROUNDING", "none"))
                price_diff_pct = None
                if product.sale_price and product.sale_price != 0:
                    price_diff_pct = (Decimal(str(suggested)) - Decimal(str(product.sale_price))) / Decimal(str(product.sale_price))
                cost_diff_pct = None
                if product.avg_cost_price and product.avg_cost_price != 0:
                    cost_diff_pct = (unit_cost - Decimal(str(product.avg_cost_price))) / Decimal(str(product.avg_cost_price))
                flag = False
                if price_diff_pct is not None and abs(price_diff_pct) >= threshold:
                    flag = True
                if not flag and cost_diff_pct is not None and abs(cost_diff_pct) >= threshold:
                    flag = True
                # Regra adicional: produto sem margem/preço definido deve ir para revisão
                if not flag and (margin == 0 or Decimal(str(product.sale_price or 0)) == 0):
                    flag = True
                if flag:
                    product.needs_review = True
                    log.info("[price_review] flagged product id=%s sku=%s name=%s suggested=%s current=%s diff=%.4f",
                             product.id, product.sku, product.name, suggested, product.sale_price, float(price_diff_pct or 0))
            except Exception:
                pass
            product.save(update_fields=["last_cost_price", "avg_cost_price", "needs_review", "updated_at"])
        except Exception:
            pass

    # Installments
    for dup in dup_list:
        nDup = str(dup.get("nDup") or "1")
        dVenc = dup.get("dVenc")
        vDup = Decimal(str(dup.get("vDup") or 0))
        due = None
        try:
            if dVenc:
                due = datetime.date.fromisoformat(dVenc)
        except Exception:
            due = None
        PurchaseInstallment.objects.create(
            invoice=inv, number=nDup, due_date=due or (issue_date or datetime.date.today()), value=vDup
        )
        log.info("[nfe_import] installment created nDup=%s value=%s", nDup, vDup)

    log.info("[nfe_import] finish invoice_id=%s items=%s", inv.id, len(det_list))
    return {"invoice_id": inv.id, "created_products": created_products}


def extract_items(xml_text: str) -> List[Dict[str, Any]]:
    """Lightweight item extraction from stored XML just for display purposes."""
    try:
        doc = xmltodict.parse(xml_text)
        nfe = (doc.get("nfeProc", {}).get("NFe") or doc.get("NFe"))
        if not nfe:
            return []
        inf = nfe["infNFe"] if "infNFe" in nfe else nfe
        det_list = inf.get("det")
        if det_list is None:
            return []
        if not isinstance(det_list, list):
            det_list = [det_list]
        items: List[Dict[str, Any]] = []
        for det in det_list:
            prod = det.get("prod", {})
            items.append(
                {
                    "cProd": str(prod.get("cProd") or ""),
                    "xProd": str(prod.get("xProd") or ""),
                    "qCom": str(prod.get("qCom") or "0"),
                    "vUnCom": str(prod.get("vUnCom") or "0"),
                    "vProd": str(prod.get("vProd") or "0"),
                    "NCM": str(prod.get("NCM") or ""),
                    "CFOP": str(prod.get("CFOP") or ""),
                    "uCom": str(prod.get("uCom") or ""),
                    "cEAN": str(prod.get("cEAN") or ""),
                    "cEANTrib": str(prod.get("cEANTrib") or ""),
                }
            )
        return items
    except Exception:
        return []
