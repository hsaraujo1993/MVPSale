import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','MVPSale.settings.dev')
import sys
django.setup()
from payment.models import CardFeeTier, CardBrand
from payment.serializers import CardFeeTierSerializer, CardBrandSerializer

brands = CardBrand.objects.all()[:20]
fees = CardFeeTier.objects.select_related('brand').all()[:20]
print('BRANDS_COUNT', brands.count())
print('FEES_COUNT', fees.count())
if brands.count()>0:
    print('BRAND_EXAMPLES', json.dumps(CardBrandSerializer(brands, many=True).data, ensure_ascii=False, indent=2))
if fees.count()>0:
    print('FEE_EXAMPLES', json.dumps(CardFeeTierSerializer(fees, many=True).data, ensure_ascii=False, indent=2))
else:
    print('NO_FEE_RECORDS')
