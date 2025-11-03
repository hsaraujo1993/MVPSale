import logging
import re
from typing import Optional, Dict, Any

import requests
from django.conf import settings


log = logging.getLogger(__name__)


def normalize_cep(cep: str) -> str:
    return re.sub(r"\D", "", cep or "")[:8]


def format_cep(cep: str) -> str:
    digits = normalize_cep(cep)
    if len(digits) == 8:
        return f"{digits[:5]}-{digits[5:]}"
    return cep or ""


def fetch_cep(cep: str) -> Optional[Dict[str, Any]]:
    """Fetch CEP data using Webmania if configured; fallback to ViaCEP if not.

    Returns a dict with keys: cep, address, city, uf, neighborhood (when available)
    or None if not resolved.
    """
    cep_digits = normalize_cep(cep)
    cep_formatted = format_cep(cep_digits)
    if not cep_digits or len(cep_digits) != 8:
        return None

    # New: support token-based auth (Bearer) for Webmania API
    token = getattr(settings, "WEBMANIA_API_TOKEN", None)
    app_key = getattr(settings, "WEBMANIA_APP_KEY", None)
    app_secret = getattr(settings, "WEBMANIA_APP_SECRET", None)
    webmania_enabled = getattr(settings, "WEBMANIA_CEP_ENABLED", True)

    # Prefer token auth if provided
    if webmania_enabled and token:
        try:
            url = f"https://webmaniabr.com/api/1/cep/{cep_digits}/"
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "cep": data.get("cep") or cep_digits,
                    "address": data.get("endereco") or data.get("logradouro") or "",
                    "neighborhood": data.get("bairro") or "",
                    "city": data.get("cidade") or data.get("localidade") or "",
                    "uf": data.get("uf") or "",
                }
            else:
                log.warning("Webmania CEP lookup failed (token auth): %s %s", resp.status_code, resp.text[:200])
        except Exception as exc:
            log.exception("Webmania CEP lookup error (token auth): %s", exc)

    # Fallback to app_key/app_secret if configured
    if webmania_enabled and app_key and app_secret:
        try:
            # Prefer the exact format confirmed to return 200
            # Example: https://webmaniabr.com/api/1/cep/05426-100/?app_key=...&app_secret=...
            url_q = (
                f"https://webmaniabr.com/api/1/cep/{cep_formatted}/?"
                f"app_key={app_key}&app_secret={app_secret}"
            )
            resp_q = requests.get(url_q, timeout=5)
            if resp_q.status_code == 200:
                data = resp_q.json()
                return {
                    "cep": data.get("cep") or cep_digits,
                    "address": data.get("endereco") or data.get("logradouro") or "",
                    "neighborhood": data.get("bairro") or "",
                    "city": data.get("cidade") or data.get("localidade") or "",
                    "uf": data.get("uf") or "",
                }

            # Fallback: header-based auth if query string fails (some environments may accept it)
            url = f"https://webmaniabr.com/api/1/cep/{cep_digits}/"
            headers = {"X-APP-KEY": app_key, "X-APP-SECRET": app_secret, "Accept": "application/json"}
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "cep": data.get("cep") or cep_digits,
                    "address": data.get("endereco") or data.get("logradouro") or "",
                    "neighborhood": data.get("bairro") or "",
                    "city": data.get("cidade") or data.get("localidade") or "",
                    "uf": data.get("uf") or "",
                }
            else:
                log.warning("Webmania CEP lookup failed (key/secret auth): %s %s", resp.status_code, resp.text[:200])
        except Exception as exc:
            log.exception("Webmania CEP lookup error (key/secret): %s", exc)

    # Fallback: ViaCEP (no key required)
    try:
        url = f"https://viacep.com.br/ws/{cep_digits}/json/"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if not data.get("erro"):
                return {
                    "cep": data.get("cep") or cep_digits,
                    "address": data.get("logradouro") or "",
                    "neighborhood": data.get("bairro") or "",
                    "city": data.get("localidade") or "",
                    "uf": data.get("uf") or "",
                }
    except Exception as exc:
        log.exception("ViaCEP lookup error: %s", exc)

    return None
