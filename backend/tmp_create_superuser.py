import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","MVPSale.settings.dev")
import django; django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='dev').exists():
    User.objects.create_superuser('dev','dev@example.com','dev12345')
print('ok')