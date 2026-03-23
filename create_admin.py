import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Master_WebSite.settings')
django.setup()

import hashlib
from core.model import AdminAccount

hashed = hashlib.sha256('admin'.encode()).hexdigest()
if not AdminAccount.objects.filter(username='admin').exists():
    AdminAccount.objects.create(username='admin', password_hash=hashed, role='admin')
    print("Default admin account created: admin / admin")
else:
    print("Default admin account already exists")
