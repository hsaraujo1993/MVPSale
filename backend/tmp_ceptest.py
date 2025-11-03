import os, json
os.environ.setdefault("DJANGO_SETTINGS_MODULE","MVPSale.settings.dev")
import django; django.setup()
from people.services.cep import fetch_cep
print(json.dumps(fetch_cep("05426-100"), ensure_ascii=False))