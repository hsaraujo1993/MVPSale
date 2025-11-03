import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MVPSale.settings.dev')
import django
django.setup()

from sale.views import OrderViewSet
from drf_spectacular.openapi import AutoSchema as SpectacularAuto

cls = OrderViewSet
schema = getattr(cls, 'schema', None)
print('schema:', schema)
print('schema type:', type(schema))
print('schema class module:', type(schema).__module__)
print('schema class name:', type(schema).__name__)
print('isinstance drf_spectacular.openapi.AutoSchema?', isinstance(schema, SpectacularAuto))
print('schema mro:', [c.__module__ + '.' + c.__name__ for c in type(schema).__mro__])

