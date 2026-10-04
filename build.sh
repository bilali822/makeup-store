#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

python manage.py shell << 'PYEOF'
import os
from store.models import Product, Category, User
from django.core.management import call_command

# دائماً نعيد تحميل الـ fixture لتحديث المسارات والصور
print(f"▶ قبل التحديث: {Product.objects.count()} منتج")
Product.objects.all().delete()
Category.objects.all().delete()
print("   ✓ تم حذف البيانات القديمة")

call_command('loaddata', 'store/fixtures/initial_data.json', verbosity=2)
print(f"✅ بعد التحديث: {Product.objects.count()} منتج")

# superuser
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
