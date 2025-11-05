import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','MVPSale.settings.dev')
import sys
django.setup()
from catalog.models import Product
from catalog.serializers import ProductSerializer
from uuid import UUID

qs = Product.objects.select_related('category','brand').all()[:10]
print('PRODUCT_COUNT', qs.count())
if qs.count()>0:
    data = ProductSerializer(qs, many=True).data
    # Convert any UUID instances to strings (defensive)
    def convert(obj):
        if isinstance(obj, dict):
            return {k: convert(v) for k,v in obj.items()}
        if isinstance(obj, list):
            return [convert(x) for x in obj]
        if isinstance(obj, UUID):
            return str(obj)
        return obj
    print(json.dumps(convert(data), ensure_ascii=False, indent=2))
else:
    print('NO_PRODUCTS')
