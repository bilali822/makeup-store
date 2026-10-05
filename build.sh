#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# ═══ تنظيف شامل: حذف السجلات + الجداول القديمة ═══
python manage.py shell << 'PYEOF'
from django.db import connection
try:
    with connection.cursor() as cursor:
        # حذف كل سجلات migrations الفواتير القديمة
        cursor.execute(
            "DELETE FROM django_migrations WHERE app='store' AND name LIKE %s",
            ['0004_%']
        )
        print(f"✅ حذف {cursor.rowcount} سجل migration قديم")

        # حذف الجداول
        for table in ['store_invoiceitem', 'store_invoice']:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"✅ DROP {table}")

    connection.commit()
except Exception as e:
    print(f"⚠️ خطأ في التنظيف: {e}")
    import traceback
    traceback.print_exc()
PYEOF

python manage.py collectstatic --noinput
python manage.py migrate --noinput --verbosity 2

python manage.py shell << 'PYEOF'
import os
from store.models import Product, User, Invoice
from django.core.management import call_command

if Product.objects.count() == 0:
    print("▶ تحميل الـ fixture...")
    try:
        call_command('loaddata', 'store/fixtures/initial_data.json', verbosity=2)
        print(f"✅ تم تحميل {Product.objects.count()} منتج")
    except Exception as e:
        print(f"⚠️ فشل: {e}")
else:
    print(f"✓ يوجد {Product.objects.count()} منتج — تخطي")

print(f"✓ جدول Invoice جاهز — {Invoice.objects.count()} فاتورة")

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
    print("⚠️ لا توجد credentials")
PYEOF
