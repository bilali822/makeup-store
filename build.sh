#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# ═══ تنظيف migration قديم (للمرة الأولى فقط) ═══
python manage.py shell << 'PYEOF'
from django.db import connection
try:
    with connection.cursor() as cursor:
        # نحذف تسجيل migration 0004 القديم إذا موجود
        cursor.execute(
            "DELETE FROM django_migrations WHERE app='store' AND name=%s",
            ['0004_customer_invoice']
        )
        deleted = cursor.rowcount
        if deleted:
            print(f"✅ تم حذف migration قديم من السجل ({deleted} صف)")
        else:
            print("✓ لا يوجد migration قديم")
except Exception as e:
    print(f"⚠️ تخطي التنظيف: {e}")
PYEOF

python manage.py collectstatic --noinput
python manage.py migrate --noinput

python manage.py shell << 'PYEOF'
import os
from store.models import Product, User
from django.core.management import call_command

if Product.objects.count() == 0:
    print("▶ تحميل الـ fixture (أول مرة)...")
    try:
        call_command('loaddata', 'store/fixtures/initial_data.json', verbosity=2)
        print(f"✅ تم تحميل {Product.objects.count()} منتج")
    except Exception as e:
        print(f"⚠️ فشل: {e}")
else:
    print(f"✓ يوجد {Product.objects.count()} منتج — تخطي")

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
