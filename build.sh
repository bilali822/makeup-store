#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# تحميل الـ fixtures إذا ما في منتجات
python manage.py shell << 'PYEOF'
import os
from store.models import Product, User
from django.core.management import call_command

# تحميل الـ fixtures
if Product.objects.count() == 0:
    print("▶ لا يوجد منتجات — تحميل الـ fixture...")
    try:
        call_command('loaddata', 'store/fixtures/initial_data.json', verbosity=2)
        print("✅ تم تحميل الـ fixture")
    except Exception as e:
        print(f"⚠️ فشل التحميل: {e}")
else:
    print(f"✓ يوجد {Product.objects.count()} منتج — تخطي")

# إنشاء superuser
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

if username and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"✅ تم إنشاء superuser: {username}")
    else:
        print(f"✓ superuser موجود: {username}")
else:
    print("⚠️ لا توجد credentials للـ superuser — تخطي")
PYEOF
