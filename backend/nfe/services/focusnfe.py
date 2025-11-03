import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from django.conf import settings
import requests
from base64 import b64encode
from django.utils import timezone
from sale.models import Order
from people.models import Customer
from catalog.models import Product
from purchase.models import SupplierProduct


log = logging.getLogger("nfe")


@dataclass
class FocusConfig:
    token: str
    base_url: str


def get_focus_config() -> Optional[FocusConfig]:
    token = getattr(settings, "FOCUSNFE_API_TOKEN", "")
    base_url = getattr(settings, "FOCUSNFE_BASE_URL", "https://homologacao.focusnfe.com.br")
    if not token:
        return None
    return FocusConfig(token=token, base_url=base_url)


class FocusNFeClient:
    def __init__(self, cfg: FocusConfig):
        self.cfg = cfg

    def is_configured(self) -> bool:
        return bool(self.cfg and self.cfg.token)

    def _auth_headers(self) -> Dict[str, str]:
        # Focus usa HTTP Basic com token como usuário e senha vazia
        token = f"{self.cfg.token}:".encode("utf-8")
        return {"Authorization": f"Basic {b64encode(token).decode('utf-8')}", "Content-Type": "application/json"}

    def _post(self, path: str, json: Dict[str, Any]) -> requests.Response:
        url = f"{self.cfg.base_url.rstrip('/')}{path}"
        log.info("[focus] POST %s", url)
        return requests.post(url, headers=self._auth_headers(), json=json, timeout=15)

    def _get(self, path: str) -> requests.Response:
        url = f"{self.cfg.base_url.rstrip('/')}{path}"
        log.info("[focus] GET %s", url)
        return requests.get(url, headers=self._auth_headers(), timeout=15)

    def _get_bytes(self, path: str, accept: str) -> requests.Response:
        url = f"{self.cfg.base_url.rstrip('/')}{path}"
        log.info("[focus] GET (bytes) %s", url)
        headers = self._auth_headers()
        headers["Accept"] = accept
        headers.pop("Content-Type", None)
        return requests.get(url, headers=headers, timeout=30)

    def submit_from_order(self, order_id: int, ref: str) -> Dict[str, Any]:
        order = Order.objects.select_related("customer", "seller").prefetch_related("items__product").get(pk=order_id)
        payload = self._build_payload(order)
        # Referência idempotente via query
        resp = self._post(f"/v2/nfe?ref={ref}", json=payload)
        try:
            data = resp.json()
        except Exception:
            data = {"status_code": resp.status_code, "text": resp.text}
        return {"http_status": resp.status_code, "data": data}

    def get_status(self, ref_or_chave: str) -> Dict[str, Any]:
        # Focus permite buscar por referência ou chave
        resp = self._get(f"/v2/nfe/{ref_or_chave}")
        try:
            data = resp.json()
        except Exception:
            data = {"status_code": resp.status_code, "text": resp.text}
        return {"http_status": resp.status_code, "data": data}

    def cancel(self, chave: str, motivo: str) -> Dict[str, Any]:
        resp = self._post(f"/v2/nfe/{chave}/cancelar", json={"justificativa": motivo})
        try:
            data = resp.json()
        except Exception:
            data = {"status_code": resp.status_code, "text": resp.text}
        return {"http_status": resp.status_code, "data": data}

    def get_xml(self, chave: str) -> Dict[str, Any]:
        resp = self._get_bytes(f"/v2/nfe/{chave}/xml", accept="application/xml")
        return {"http_status": resp.status_code, "content": resp.content, "content_type": resp.headers.get("Content-Type", "application/xml")}

    def get_danfe(self, chave: str) -> Dict[str, Any]:
        resp = self._get_bytes(f"/v2/nfe/{chave}/danfe", accept="application/pdf")
        return {"http_status": resp.status_code, "content": resp.content, "content_type": resp.headers.get("Content-Type", "application/pdf")}

    def _build_payload(self, order: Order) -> Dict[str, Any]:
        customer: Optional[Customer] = order.customer
        # Defaults via env
        cfop_default = getattr(settings, "NFE_DEFAULT_CFOP", "5102")
        ncm_default = getattr(settings, "NFE_DEFAULT_NCM", "00000000")
        cest_default = getattr(settings, "NFE_DEFAULT_CEST", "")
        unidade_default = getattr(settings, "NFE_DEFAULT_UNIT", "UN")
        icms_cst_default = getattr(settings, "NFE_DEFAULT_ICMS_CST", "102")
        icms_origem_default = int(getattr(settings, "NFE_DEFAULT_ICMS_ORIG", 0))

        items: List[Dict[str, Any]] = []
        for idx, it in enumerate(order.items.select_related("product"), start=1):
            prod: Product = it.product
            # Try map from SupplierProduct (fallback to defaults)
            sp = SupplierProduct.objects.filter(product=prod).first()
            ncm = (sp.ncm if sp and sp.ncm else ncm_default)
            cest = (sp.cest if sp and sp.cest else cest_default)
            cfop = cfop_default
            item = {
                "numero_item": idx,
                "codigo_produto": prod.sku or str(prod.id),
                "descricao": prod.name,
                "ncm": ncm,
                "cest": cest or None,
                "cfop": cfop,
                "unidade_comercial": unidade_default,
                "quantidade_comercial": float(it.quantity),
                "valor_unitario_comercial": float(it.unit_price),
                "unidade_tributavel": unidade_default,
                "quantidade_tributavel": float(it.quantity),
                "valor_unitario_tributavel": float(it.unit_price),
                "icms_situacao_tributaria": icms_cst_default,
                "icms_origem": icms_origem_default,
            }
            items.append(item)

        cliente = {}
        if customer:
            cpf_cnpj = customer.cpf_cnpj or ""
            cliente = {
                "nome": customer.name,
                ("cpf" if len(cpf_cnpj) == 11 else "cnpj"): cpf_cnpj,
                "email": customer.email or None,
                "endereco": customer.address or None,
                "numero": None,
                "bairro": customer.city or None,  # ajustar quando tivermos bairro
                "municipio": customer.city or None,
                "uf": customer.uf or None,
                "cep": customer.cep or None,
            }

        payload = {
            "natureza_operacao": getattr(settings, "NFE_NATUREZA_OPERACAO", "VENDA"),
            "serie": getattr(settings, "NFE_SERIE", "1"),
            "numero": None,  # Focus atribui pela referência/numeração interna se configurado, ou podemos gerenciar
            "data_emissao": timezone.now().strftime("%Y-%m-%dT%H:%M:%S%z"),
            "local_destino": 1,
            "consumidor_final": 1,
            "presenca_comprador": 1,
            "modalidade_frete": 0,
            "cliente": cliente or None,
            "items": items,
            # Totais/impostos podem ser calculados pelo provider com base nos itens; ajustaremos conforme testes
        }
        return payload
