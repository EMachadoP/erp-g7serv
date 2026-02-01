import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

print("DATABASES configuration:")
print(settings.DATABASES)
