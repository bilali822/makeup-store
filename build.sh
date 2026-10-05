#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

python manage.py shell << 'PYEOF'
import os
from store.models import Product, User
from django.core.management import call_command

if Product.objects.count() == 0:
    print("▶ لا يوجد منتجات — تحميل الـ fixture (أول مرة)...")
    try:
        call_command('loaddata', 'store/fixtures/initial_data.json', verbosity=2)
        print(f"✅ تم تحميل {Product.objects.count()} منتج")
    except Exception as e:
        print(f"⚠️ فشل تحميل الـ fixture: {e}")
else:
    print(f"✓ يوجد {Product.objects.count()} منتج — تخطي (الحفاظ على البيانات)")

username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

if username and password:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'email': email, 'is_staff': True, 'is_superuser': True}
    )
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"✅ Superuser {'created' if created else 'updated'}: {username}")
else:
    print("⚠️ لا توجد credentials للـ superuser")
PYEOF
