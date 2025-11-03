import os
import sys
from pathlib import Path


def main():
    settings = sys.argv[1] if len(sys.argv) > 1 else "MVPSale.settings.dev"
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings)

    import django
    from django.core.management import call_command
    from django.contrib.auth import get_user_model
    from django.test import Client

    django.setup()

    # migrate
    call_command("migrate", interactive=False, verbosity=0)

    # ensure user
    User = get_user_model()
    username = os.getenv("TEST_USERNAME", "admin")
    password = os.getenv("TEST_PASSWORD", "admin123")
    if not User.objects.filter(username=username).exists():
        User.objects.create_user(username=username, password=password, is_staff=True, is_superuser=True)
        print("created user:", username)
    else:
        print("user exists:", username)

    c = Client()
    # generate JWT directly
    from rest_framework_simplejwt.tokens import RefreshToken
    user = User.objects.get(username=username)
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    print("token ok")

    headers = {"HTTP_AUTHORIZATION": f"Bearer {access_token}"}

    import json
    # import XML from sample file if exists
    sample = Path.cwd() / "35251058840448000284550010001958131902274946.xml"
    if sample.exists():
        xml_text = sample.read_text(encoding="utf-8", errors="ignore")
        resp = c.post("/api/purchase/import-xml/", data=json.dumps({"xml_text": xml_text}), content_type="application/json", **headers)
        print("import status:", resp.status_code)
        if resp.status_code not in (200, 201):
            print("import error:", resp.content[:300])
    else:
        print("sample XML not found, skipping import")

    # list supplier invoices
    resp = c.get("/api/purchase/invoices/", **headers)
    print("list supplier invoices:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        count = data.get("count", len(data) if isinstance(data, list) else 0)
        print("supplier invoices count:", count)
    else:
        print("list error:", resp.content[:300])

    # list nfe invoices (sales) just to ensure route OK
    resp = c.get("/api/nfe/invoices/", **headers)
    print("list nfe invoices:", resp.status_code)


if __name__ == "__main__":
    main()
