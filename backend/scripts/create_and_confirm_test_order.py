import json
from decimal import Decimal

# This script is intended to be run via: python backend/manage.py shell < backend/scripts/create_and_confirm_test_order.py

from sale.models import Order, OrderItem, confirm_order
from people.models import Customer, Seller
from payment.models import PaymentMethod
from catalog.models import Product

# Find sample records
cust = Customer.objects.first()
sel = Seller.objects.first()
pm = PaymentMethod.objects.filter().first()
prod = Product.objects.filter().first()

if not (cust and sel and pm and prod):
    print('MISSING_ENTITIES', 'customer' if not cust else '', 'seller' if not sel else '', 'payment_method' if not pm else '', 'product' if not prod else '')
else:
    # Create order
    o = Order.objects.create(customer=cust, seller=sel, payment_method=pm, order_discount_abs=Decimal('1.00'))
    # Build payment_metadata with fee_percent and fee_value (simulate frontend)
    # Use fee_percent 2.5% and compute fee_value from base total after adding item below
    meta = { 'uuid': str(pm.uuid), 'name': pm.name, 'type': pm.type, 'fee_percent': '2.50', 'installments': 2, 'card_brand': None }
    o.payment_metadata = meta
    o.save()

    # Add an item
    it = OrderItem.objects.create(order=o, product=prod, quantity=1, unit_price=Decimal('10.00'))
    # recalc already called by save of item
    # Now compute and set fee_value in metadata as absolute number based on current baseTotal
    base_total = o.total
    fee_pct = Decimal('2.50')
    computed_fee = (base_total * fee_pct / Decimal('100')).quantize(Decimal('0.01'))
    o.payment_metadata['fee_value'] = format(computed_fee, 'f')
    o.save(update_fields=['payment_metadata'])

    print('CREATED_ORDER_UUID', str(o.uuid))
    print('BEFORE_CONFIRM', 'subtotal', o.subtotal, 'total', o.total, 'payment_metadata', json.dumps(o.payment_metadata))
    # confirm
    try:
        confirm_order(o)
        o.refresh_from_db()
        print('AFTER_CONFIRM', 'status', o.status, 'payment_fee', o.payment_fee, 'payment_metadata', json.dumps(o.payment_metadata))
    except Exception as e:
        print('CONFIRM_ERROR', repr(e))
