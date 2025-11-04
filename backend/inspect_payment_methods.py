import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','MVPSale.settings.dev')
import sys
django.setup()
from payment.models import PaymentMethod
from payment.serializers import PaymentMethodSerializer

qs = PaymentMethod.objects.all()[:50]
print('PAYMENT_METHOD_COUNT', qs.count())
if qs.count()>0:
    print(json.dumps(PaymentMethodSerializer(qs, many=True).data, ensure_ascii=False, indent=2))
else:
    print('NO_PAYMENT_METHODS')

