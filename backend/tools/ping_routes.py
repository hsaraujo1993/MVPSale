import os
import sys
from typing import List, Tuple


def main():
    # minimal online checks using Django test client
    settings = sys.argv[1] if len(sys.argv) > 1 else "MVPSale.settings.dev"
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings)

    import django
    from django.test import Client

    django.setup()
    c = Client()

    checks: List[Tuple[str, int]] = [
        ("/", 200),
        ("/login", 200),
        ("/nfe", 200),
        ("/catalog", 200),
        ("/api/health/", 200),
        ("/api/schema/", 200),
        ("/api/nfe/invoices/", 401),
        ("/api/purchase/invoices/", 401),
        ("/api/purchase/import-xml/", 401),
        ("/api/sale/orders/", 401),
    ]

    ok = True
    for path, expected in checks:
        resp = c.get(path)
        status = resp.status_code
        result = "OK" if status == expected else f"FAIL (got {status}, want {expected})"
        print(f"{path}\t{result}")
        if status != expected:
            ok = False

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

