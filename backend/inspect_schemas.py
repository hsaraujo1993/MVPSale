import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MVPSale.settings.dev')
django.setup()

from django.urls import get_resolver
from drf_spectacular.openapi import AutoSchema as SpectacularAuto

resolver = get_resolver()
views = set()

def walk(patterns):
    for p in patterns:
        if hasattr(p, 'url_patterns'):
            walk(p.url_patterns)
        else:
            callback = getattr(p, 'callback', None)
            if callback:
                cls = getattr(callback, 'cls', None)
                if cls:
                    views.add(cls)

walk(resolver.url_patterns)

for v in sorted(views, key=lambda x: x.__name__):
    schema = getattr(v, 'schema', None)
    typ = type(schema)
    ok = isinstance(schema, SpectacularAuto)
    print(f"{v.__module__}.{v.__name__} -> schema type: {typ} | spectacular?: {ok}")

# Additionally, print any views whose schema is not drf_spectacular.openapi.AutoSchema
print('\nViews with non-drf_spectacular AutoSchema (or missing schema):')
for v in sorted(views, key=lambda x: x.__name__):
    schema = getattr(v, 'schema', None)
    if not isinstance(schema, SpectacularAuto):
        print(f"- {v.__module__}.{v.__name__}: {type(schema)} -> {repr(schema)}")
