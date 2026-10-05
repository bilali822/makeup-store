from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.conf import settings
import base64
import requests
from .models import User, Category, Product, Order


# ═══════════════════════════════════════════
# IMGBB UPLOAD HELPER
# ═══════════════════════════════════════════
def upload_to_imgbb(image_file):
    """رفع الصورة لـ ImgBB وإرجاع الرابط"""
    api_key = getattr(settings, 'IMGBB_API_KEY', None)
    if not api_key:
        return None
    try:
        image_file.seek(0)
        encoded = base64.b64encode(image_file.read()).decode('utf-8')
        response = requests.post(
            'https://api.imgbb.com/1/upload',
            data={
                'key': api_key,
                'image': encoded,
                'name': getattr(image_file, 'name', 'image'),
            },
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data['data']['url']
    except Exception as e:
        print(f"ImgBB upload failed: {e}")
    return None


# ═══════════════════════════════════════════
# USER ADMIN
# ═══════════════════════════════════════════
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('معلومات إضافية', {'fields': ('is_seller', 'phone', 'address')}),
    )
    list_display = ['username', 'email', 'is_seller_badge', 'is_staff', 'date_joined']
    list_filter = ['is_seller', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'phone']

    @admin.display(description='بائع')
    def is_seller_badge(self, obj):
        if obj.is_seller:
            return format_html(
                '<span style="background:#10b981;color:white;padding:3px 10px;'
                'border-radius:12px;font-size:11px;">✓ بائع</span>'
            )
        return format_html(
            '<span style="background:#e5e7eb;color:#6b7280;padding:3px 10px;'
            'border-radius:12px;font-size:11px;">مشتري</span>'
        )


# ═══════════════════════════════════════════
# CATEGORY ADMIN
# ═══════════════════════════════════════════
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ['icon_preview', 'name', 'slug', 'product_count']
    search_fields = ['name']

    @admin.display(description='الأيقونة')
    def icon_preview(self, obj):
        return format_html(
            '<i class="fas {}" style="font-size:20px;color:#ec4899;"></i>',
            obj.icon
        )

    @admin.display(description='عدد المنتجات')
    def product_count(self, obj):
        count = obj.product_set.count()
        return format_html(
            '<span style="background:#fce7f3;color:#be185d;padding:3px 10px;'
            'border-radius:12px;font-weight:600;">{}</span>',
            count
        )


# ═══════════════════════════════════════════
# PRODUCT ADMIN
# ═══════════════════════════════════════════
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'image_preview', 'title', 'category_badge', 'owner',
        'price_display', 'stock_display', 'is_active', 'created_at'
    ]
    list_filter = ['category', 'is_active', 'owner', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_active']
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('title', 'description', 'category', 'owner')
        }),
        ('التسعير والمخزون', {
            'fields': ('price', 'stock', 'is_active')
        }),
        ('الصورة', {
            'fields': ('image', 'image_url'),
            'description': '📸 عند رفع صورة جديدة، سيتم رفعها تلقائياً إلى ImgBB وستظل محفوظة بشكل دائم.'
        }),
    )

    actions = ['activate_products', 'deactivate_products']

    @admin.display(description='الصورة')
    def image_preview(self, obj):
        url = obj.display_image
        if url:
            return format_html(
                '<img src="{}" style="width:50px;height:50px;'
                'object-fit:cover;border-radius:8px;border:1px solid #e5e7eb;" />',
                url
            )
        return format_html(
            '<div style="width:50px;height:50px;background:#f3f4f6;'
            'border-radius:8px;text-align:center;line-height:50px;'
            'color:#9ca3af;font-size:20px;">📷</div>'
        )

    @admin.display(description='الفئة')
    def category_badge(self, obj):
        if obj.category:
            return format_html(
                '<span style="background:#fce7f3;color:#be185d;padding:4px 10px;'
                'border-radius:12px;font-size:12px;font-weight:600;">{}</span>',
                obj.category.name
            )
        return '—'

    @admin.display(description='السعر')
    def price_display(self, obj):
        return format_html(
            '<span style="color:#059669;font-weight:700;">${}</span>',
            obj.price
        )

    @admin.display(description='المخزون')
    def stock_display(self, obj):
        if obj.stock == 0:
            color, bg = '#ef4444', '#fee2e2'
        elif obj.stock < 5:
            color, bg = '#f59e0b', '#fef3c7'
        else:
            color, bg = '#10b981', '#d1fae5'
        return format_html(
            '<span style="background:{};color:{};padding:4px 10px;'
            'border-radius:12px;font-weight:600;font-size:12px;">{}</span>',
            bg, color, obj.stock
        )

    def save_model(self, request, obj, form, change):
        """عند حفظ المنتج — رفع الصورة الجديدة لـ ImgBB"""
        if 'image' in form.changed_data and obj.image:
            try:
                obj.image.seek(0)
                url = upload_to_imgbb(obj.image)
                if url:
                    obj.image_url = url
                    obj.image = None
                    self.message_user(
                        request,
                        f'✅ تم رفع الصورة إلى ImgBB بنجاح'
                    )
                else:
                    self.message_user(
                        request,
                        '⚠️ تعذّر رفع الصورة — تحقق من IMGBB_API_KEY',
                        level='WARNING'
                    )
            except Exception as e:
                self.message_user(
                    request,
                    f'⚠️ خطأ في رفع الصورة: {e}',
                    level='ERROR'
                )
        super().save_model(request, obj, form, change)

    @admin.action(description='✓ تفعيل المنتجات المحددة')
    def activate_products(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ تم تفعيل {updated} منتج')

    @admin.action(description='✗ تعطيل المنتجات المحددة')
    def deactivate_products(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'✅ تم تعطيل {updated} منتج')


# ═══════════════════════════════════════════
# ORDER ADMIN
# ═══════════════════════════════════════════
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'buyer', 'product', 'quantity',
        'total_display', 'status_badge', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['buyer__username', 'product__title']
    # list_editable = ['status']  # disabled: status_badge in use
    date_hierarchy = 'created_at'

    @admin.display(description='الإجمالي')
    def total_display(self, obj):
        return format_html(
            '<span style="color:#059669;font-weight:700;">${}</span>',
            obj.total
        )

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        colors = {
            'pending': ('#f59e0b', '#fef3c7', '⏳ قيد الانتظار'),
            'confirmed': ('#3b82f6', '#dbeafe', '✓ مؤكد'),
            'shipped': ('#8b5cf6', '#ede9fe', '🚚 تم الشحن'),
            'delivered': ('#10b981', '#d1fae5', '✅ تم التسليم'),
            'cancelled': ('#ef4444', '#fee2e2', '✗ ملغى'),
        }
        color, bg, label = colors.get(obj.status, ('#6b7280', '#f3f4f6', obj.status))
        return format_html(
            '<span style="background:{};color:{};padding:4px 12px;'
            'border-radius:12px;font-weight:600;font-size:12px;">{}</span>',
            bg, color, label
        )


# ═══════════════════════════════════════════
# ADMIN SITE CUSTOMIZATION
# ═══════════════════════════════════════════
admin.site.site_header = "SB by Sabah — لوحة التحكم"
admin.site.site_title = "SB by Sabah"
admin.site.index_title = "مرحباً بك في لوحة تحكم المتجر ✨"
