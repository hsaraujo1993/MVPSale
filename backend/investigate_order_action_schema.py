import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MVPSale.settings.dev')
import django
django.setup()

from django.urls import get_resolver
from drf_spectacular.plumbing import get_class
from drf_spectacular.openapi import AutoSchema as SpectacularAuto

resolver = get_resolver()
for p in resolver.url_patterns:
    if hasattr(p, 'url_patterns'):
        for pp in p.url_patterns:
            try:
                path = str(pp.pattern)
            except Exception:
                continue
            if 'sale/orders' in path and 'action' in path:
                callback = pp.callback
                print('FOUND pattern:', path)
                print('callback:', callback)
                print('callback.cls:', getattr(callback, 'cls', None))
                cls = getattr(callback, 'cls', None)
                print('callback.cls.schema attr:', getattr(cls, 'schema', None))
                # find method name
                actions = getattr(callback, 'actions', None)
                print('callback.actions:', actions)
                # create view instance like SchemaGenerator.create_view does
                from drf_spectacular.generators import SchemaGenerator
                gen = SchemaGenerator()
                try:
                    view = gen.create_view(callback, 'POST')
                except Exception as e:
                    print('create_view raised:', e)
                    view = None
                print('view:', view)
                if view is not None:
                    print('view.schema:', getattr(view, 'schema', None))
                    print('type(view.schema):', type(getattr(view,'schema',None)))
                break

print('done')

