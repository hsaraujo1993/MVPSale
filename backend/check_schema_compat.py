import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MVPSale.settings.dev')
import django
django.setup()

from django.conf import settings
from rest_framework.settings import api_settings
from sale.views import OrderViewSet
import drf_spectacular.openapi as spec_openapi

schema = getattr(OrderViewSet, 'schema', None)
print('OrderViewSet.schema:', schema)
print('type(schema):', type(schema))
print('schema module:', type(schema).__module__)
print('schema class is spec_openapi.AutoSchema?:', isinstance(schema, spec_openapi.AutoSchema))
print('api_settings.DEFAULT_SCHEMA_CLASS:', api_settings.DEFAULT_SCHEMA_CLASS)
print('api_settings.DEFAULT_SCHEMA_CLASS.__module__:', api_settings.DEFAULT_SCHEMA_CLASS.__module__)
print('api_settings.DEFAULT_SCHEMA_CLASS == spec_openapi.AutoSchema?:', api_settings.DEFAULT_SCHEMA_CLASS is spec_openapi.AutoSchema)
print('api_settings.DEFAULT_SCHEMA_CLASS mro:', api_settings.DEFAULT_SCHEMA_CLASS.__mro__)
print('spec_openapi.AutoSchema mro:', spec_openapi.AutoSchema.__mro__)

