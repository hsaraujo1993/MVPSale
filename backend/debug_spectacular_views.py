import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MVPSale.settings.dev')
import django
django.setup()

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.openapi import AutoSchema as SpectacularAuto
from rest_framework.settings import api_settings

gen = SchemaGenerator()
try:
    gen._initialise_endpoints()
except Exception as e:
    print('Error initialising endpoints:', e)

print('Total endpoints:', len(gen.endpoints))

for idx, (path, path_regex, method, callback) in enumerate(gen.endpoints):
    try:
        view = gen.create_view(callback, method)
    except Exception as e:
        print(f"[{idx}] create_view FAILED for {callback}: {e}")
        continue
    schema = getattr(view, 'schema', None)
    ok = isinstance(schema, SpectacularAuto)
    print(f"[{idx}] path={path} method={method} callback={getattr(callback,'cls',callback)} -> schema type: {type(schema)} ok? {ok}")
    if not ok:
        print('  view.schema repr:', repr(schema))
        print('  api_settings.DEFAULT_SCHEMA_CLASS:', api_settings.DEFAULT_SCHEMA_CLASS)
        print('  DEFAULT_SCHEMA_CLASS mro:', api_settings.DEFAULT_SCHEMA_CLASS.__mro__)
        break

print('done')

