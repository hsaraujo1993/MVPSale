import os
import sys
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MVPSale.settings.dev")

import django  # noqa: E402

django.setup()

from people.services.cep import fetch_cep  # noqa: E402


def main():
    cep = sys.argv[1] if len(sys.argv) > 1 else "01001-000"
    res = fetch_cep(cep)
    print(json.dumps({"input": cep, "result": res}, ensure_ascii=False))
    if not res:
        sys.exit(2)


if __name__ == "__main__":
    main()

