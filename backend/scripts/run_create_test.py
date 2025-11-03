import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MVPSale.settings.dev')
import django
django.setup()

exec(open(os.path.join(os.path.dirname(__file__), 'create_and_confirm_test_order.py')).read())
print('\nSCRIPT_FINISHED')
