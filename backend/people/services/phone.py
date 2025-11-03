import re


def normalize_phone(phone: str) -> str:
    return re.sub(r"\D", "", phone or "")


def format_phone(phone: str) -> str:
    digits = normalize_phone(phone)
    # Use last 11/10 digits to avoid country code if present
    if len(digits) >= 11:
        d = digits[-11:]
        area = d[:2]
        body = d[2:]
        return f"({area}) {body[:5]}-{body[5:]}"
    if len(digits) == 10:
        area = digits[:2]
        body = digits[2:]
        return f"({area}) {body[:4]}-{body[4:]}"
    if len(digits) == 9:
        return f"{digits[:5]}-{digits[5:]}"
    if len(digits) == 8:
        return f"{digits[:4]}-{digits[4:]}"
    return phone or ""

