import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MVPSale.settings.dev')
import django
django.setup()

from people.models import Customer, Seller
from payment.models import PaymentMethod
from catalog.models import Product

print('Customers:', Customer.objects.count())
print('First customer:', getattr(Customer.objects.first(), 'uuid', None))
print('Sellers:', Seller.objects.count())
print('First seller:', getattr(Seller.objects.first(), 'uuid', None))
print('PaymentMethods:', PaymentMethod.objects.count())
pm = PaymentMethod.objects.first()
print('First payment method uuid:', getattr(pm, 'uuid', None) if pm else None)
print('Products:', Product.objects.count())
print('First product:', getattr(Product.objects.first(), 'uuid', None))

