import os
import sys
import json

# Ensure backend package on path and Django settings
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MVPSale.settings.dev')

import django
django.setup()

from sale.models import Order

uuids = [
    '3c3d0295-a43f-499f-a714-9982f6792656',
    '571d3f9b-9f5d-4a2a-accd-55de3e1d5b38',
    'cf8ad03f-571c-4057-b732-c2674b440ca0'
]

for u in uuids:
    try:
        o = Order.objects.get(uuid=u)
        print('FOUND', u)
        print('payment_metadata:', json.dumps(o.payment_metadata or {}, ensure_ascii=False))
        print('payment_fee:', str(o.payment_fee))
        print('subtotal,total,discount_total:', str(o.subtotal), str(o.total), str(o.discount_total))
        print('status:', o.status)
        print('sales_order:', o.sales_order)
        print('---')
    except Exception as e:
        print('NOTFOUND', u, repr(e))
