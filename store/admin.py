from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.conf import settings
from django.db.models import Sum, Avg, F
from django.urls import reverse
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    RangeDateFilter, ChoicesDropdownFilter, RelatedDropdownFilter, RangeNumericFilter,
)
from unfold.decorators import display, action
from .models import User, Category, Product, Order, Invoice, InvoiceItem, Customer
import base64, csv, requests
from django.http import HttpResponse


def upload_to_imgbb(image_file):
    api_key = getattr(settings, 'IMGBB_API_KEY', None)
    if not api_key:
        return None
    try:
        image_file.seek(0)
        encoded = base64.b64encode(image_file.read()).decode('utf-8')
        response = requests.post(
            'https://api.imgbb.com/1/upload',
            data={'key': api_key, 'image': encoded, 'name': getattr(image_file, 'name', 'image')},
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data['data']['url']
    except Exception as e:
        print(f"ImgBB failed: {e}")
    return None


class LowStockFilter(admin.SimpleListFilter):
    title = 'حالة المخزون'
    parameter_name = 'stock_status'
    def lookups(self, request, model_admin):
        return [('low', 'منخفض (< 5)'), ('out', 'نفذ (0)'), ('ok', 'جيد (5+)')]
    def queryset(self, request, queryset):
        if self.value() == 'low':
            return queryset.filter(stock__lt=5, stock__gt=0)
        if self.value() == 'out':
            return queryset.filter(stock=0)
        if self.value() == 'ok':
            return queryset.filter(stock__gte=5)


class HasImageFilter(admin.SimpleListFilter):
    title = 'الصورة'
    parameter_name = 'has_image'
    def lookups(self, request, model_admin):
        return [('yes', 'مع صورة'), ('no', 'بدون صورة')]
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(image_url='').exclude(image_url__isnull=True)
        if self.value() == 'no':
            return queryset.filter(image_url__in=['', None])


def dashboard_callback(request, context):
    agg = Product.objects.aggregate(avg=Avg('price'), total_value=Sum(F('price') * F('stock')))
    context.update({
        "kpi": [
            {"title": "المنتجات", "metric": Product.objects.count(), "footer": f"{Product.objects.filter(is_active=True).count()} نشط", "icon": "📦"},
            {"title": "الفواتير", "metric": Invoice.objects.count(), "footer": f"{Invoice.objects.filter(delivery_status='pending').count()} قيد المعالجة", "icon": "🧾"},
            {"title": "العملاء", "metric": Customer.objects.filter(is_seller=False).count(), "footer": "إجمالي", "icon": "👥"},
            {"title": "مخزون منخفض", "metric": Product.objects.filter(stock__lt=5).count(), "footer": f"{Product.objects.filter(stock=0).count()} نفذ", "icon": "⚠️"},
        ],
        "recent_orders": Invoice.objects.select_related('customer').order_by('-created_at')[:5],
        "recent_products": Product.objects.select_related('category').order_by('-created_at')[:5],
        "low_stock_products": Product.objects.filter(stock__lt=5).order_by('stock')[:5],
        "avg_price": agg['avg'] or 0,
        "total_stock_value": agg['total_value'] or 0,
        "active_products": Product.objects.filter(is_active=True).count(),
        "inactive_products": Product.objects.filter(is_active=False).count(),
    })
    return context


@action(description='📥 تصدير CSV')
def export_as_csv(modeladmin, request, queryset):
    meta = modeladmin.model._meta
    field_names = [f.name for f in meta.fields]
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename={meta.verbose_name_plural}.csv'
    writer = csv.writer(response)
    writer.writerow(field_names)
    for obj in queryset:
        writer.writerow([getattr(obj, f) for f in field_names])
    return response


class InvoiceItemInline(TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price']
    autocomplete_fields = ['product']


class OrderInline(TabularInline):
    model = Order
    fk_name = 'product'
    extra = 0
    fields = ['buyer', 'quantity', 'status', 'created_at']
    readonly_fields = ['created_at']
    show_change_link = True


class ProductInline(TabularInline):
    model = Product
    extra = 0
    fields = ['title', 'price', 'stock', 'is_active']
    show_change_link = True


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('معلومات إضافية', {'fields': ('is_seller', 'phone', 'address')}),
    )
    list_display = ['username', 'email', 'is_seller_badge', 'is_staff', 'product_count', 'date_joined']
    list_filter = ['is_seller', 'is_staff', 'is_active', ('date_joined', RangeDateFilter)]
    search_fields = ['username', 'email', 'phone']

    @display(description='بائع', label={'بائع': 'success', 'مشتري': 'info'})
    def is_seller_badge(self, obj):
        return 'بائع' if obj.is_seller else 'مشتري'

    @display(description='المنتجات')
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ['username', 'full_name', 'phone', 'invoice_count', 'total_spent', 'last_login', 'is_active']
    list_filter = [('date_joined', RangeDateFilter), 'is_active']
    search_fields = ['username', 'email', 'phone', 'address', 'first_name', 'last_name']
    ordering = ['-date_joined']
    readonly_fields = ['date_joined', 'last_login']

    fieldsets = (
        ('معلومات أساسية', {'fields': ('username', 'email', 'first_name', 'last_name', 'phone')}),
        ('العنوان', {'fields': ('address',)}),
        ('الحالة', {'fields': ('is_active', 'date_joined', 'last_login')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_seller=False)

    def has_add_permission(self, request):
        return False

    @display(description='الاسم')
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or '—'

    @display(description='عدد الفواتير')
    def invoice_count(self, obj):
        return Invoice.objects.filter(customer=obj).count()

    @display(description='إجمالي الشراء')
    def total_spent(self, obj):
        total = Invoice.objects.filter(customer=obj).aggregate(t=Sum('total'))['t'] or 0
        return f"${total:.2f}"


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ['name', 'slug', 'product_count_badge']
    search_fields = ['name']
    inlines = [ProductInline]

    @display(description='عدد المنتجات', label=True)
    def product_count_badge(self, obj):
        return obj.product_set.count()


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['image_preview', 'title', 'category_badge', 'owner', 'price_display', 'stock_badge', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'owner', LowStockFilter, HasImageFilter, ('price', RangeNumericFilter), ('created_at', RangeDateFilter), ('category', RelatedDropdownFilter)]
    search_fields = ['title', 'description', 'owner__username']
    list_editable = ['is_active']
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_select_related = ['category', 'owner']
    actions = ['activate_products', 'deactivate_products', export_as_csv]
    inlines = [OrderInline]

    fieldsets = (
        ('معلومات أساسية', {'fields': ('title', 'description', 'category', 'owner')}),
        ('التسعير والمخزون', {'fields': ('price', 'stock', 'is_active')}),
        ('الصورة', {'fields': ('image', 'image_url'), 'description': '📸 عند رفع صورة جديدة، سيتم رفعها تلقائياً إلى ImgBB.'}),
    )

    @display(description='الصورة')
    def image_preview(self, obj):
        url = obj.display_image
        if url:
            return format_html('<img src="{}" style="width:45px;height:45px;object-fit:cover;border-radius:8px;border:1px solid #e5e7eb;" />', url)
        return format_html('<div style="width:45px;height:45px;background:#f3f4f6;border-radius:8px;text-align:center;line-height:45px;color:#9ca3af;font-size:18px;">📷</div>')

    @display(description='الفئة')
    def category_badge(self, obj):
        return obj.category.name if obj.category else '—'

    @display(description='السعر', ordering='price')
    def price_display(self, obj):
        return f"${obj.price}"

    @display(description='المخزون', ordering='stock', label={'0': 'danger', '1': 'warning', '5': 'success'})
    def stock_badge(self, obj):
        return str(obj.stock)

    def save_model(self, request, obj, form, change):
        if 'image' in form.changed_data and obj.image:
            try:
                obj.image.seek(0)
                url = upload_to_imgbb(obj.image)
                if url:
                    obj.image_url = url
                    obj.image = None
                    self.message_user(request, '✅ تم رفع الصورة إلى ImgBB')
                else:
                    self.message_user(request, '⚠️ فشل رفع الصورة', level='WARNING')
            except Exception as e:
                self.message_user(request, f'⚠️ خطأ: {e}', level='ERROR')
        super().save_model(request, obj, form, change)

    @action(description='✓ تفعيل المحددة')
    def activate_products(self, request, queryset):
        n = queryset.update(is_active=True)
        self.message_user(request, f'✅ تم تفعيل {n} منتج')

    @action(description='✗ تعطيل المحددة')
    def deactivate_products(self, request, queryset):
        n = queryset.update(is_active=False)
        self.message_user(request, f'✅ تم تعطيل {n} منتج')


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ['id', 'buyer', 'product', 'quantity', 'total_display', 'status_badge', 'created_at']
    list_filter = [('status', ChoicesDropdownFilter), ('created_at', RangeDateFilter), 'buyer']
    search_fields = ['buyer__username', 'product__title', 'id']
    date_hierarchy = 'created_at'
    list_select_related = ['buyer', 'product']
    actions = ['mark_confirmed', 'mark_shipped', 'mark_delivered', export_as_csv]

    @display(description='الإجمالي')
    def total_display(self, obj):
        return f"${obj.total}"

    @display(description='الحالة', ordering='status', label={
        'pending': 'warning', 'confirmed': 'info', 'shipped': 'primary',
        'delivered': 'success', 'cancelled': 'danger',
    })
    def status_badge(self, obj):
        return obj.get_status_display()

    @action(description='✓ تأكيد')
    def mark_confirmed(self, request, queryset):
        n = queryset.update(status='confirmed')
        self.message_user(request, f'✅ {n} طلب')

    @action(description='🚚 شحن')
    def mark_shipped(self, request, queryset):
        n = queryset.update(status='shipped')
        self.message_user(request, f'✅ {n} طلب')

    @action(description='✅ تسليم')
    def mark_delivered(self, request, queryset):
        n = queryset.update(status='delivered')
        self.message_user(request, f'✅ {n} طلب')


@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ['invoice_number', 'customer_link', 'issue_date', 'items_count', 'total_display', 'delivery_badge', 'payment_badge']
    list_filter = [
        ('delivery_status', ChoicesDropdownFilter),
        ('payment_status', ChoicesDropdownFilter),
        ('issue_date', RangeDateFilter),
    ]
    search_fields = ['invoice_number', 'customer__username', 'customer__phone']
    date_hierarchy = 'issue_date'
    readonly_fields = ['invoice_number', 'subtotal', 'total', 'created_at', 'updated_at']
    list_select_related = ['customer']
    list_per_page = 25
    inlines = [InvoiceItemInline]
    autocomplete_fields = ['customer']
    actions = [
        'mark_pending', 'mark_preparing', 'mark_shipped', 'mark_delivered', 'mark_returned',
        'mark_unpaid', 'mark_partial', 'mark_paid', 'mark_refunded',
        export_as_csv,
    ]

    fieldsets = (
        ('معلومات الفاتورة', {'fields': ('invoice_number', 'customer', 'issue_date', 'delivery_date')}),
        ('الحالات', {'fields': ('delivery_status', 'payment_status')}),
        ('المبالغ', {'fields': ('subtotal', 'discount', 'delivery_fee', 'total')}),
        ('ملاحظات', {'fields': ('notes',)}),
        ('معلومات', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @display(description='العميل')
    def customer_link(self, obj):
        return format_html(
            '<a href="{}" class="text-primary-600 hover:underline font-medium">{}</a>',
            reverse('admin:store_customer_change', args=[obj.customer.id]),
            obj.customer.username
        )

    @display(description='العناصر')
    def items_count(self, obj):
        return obj.items.count()

    @display(description='الإجمالي', ordering='total')
    def total_display(self, obj):
        return format_html('<span class="font-bold text-green-600">${}</span>', obj.total)

    @display(description='التوصيل', ordering='delivery_status', label={
        'pending': 'warning', 'preparing': 'info', 'shipped': 'primary',
        'delivered': 'success', 'returned': 'danger',
    })
    def delivery_badge(self, obj):
        return obj.get_delivery_status_display()

    @display(description='الدفع', ordering='payment_status', label={
        'unpaid': 'danger', 'partial': 'warning', 'paid': 'success', 'refunded': 'secondary',
    })
    def payment_badge(self, obj):
        return obj.get_payment_status_display()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalculate()

    @action(description='⏳ قيد المعالجة')
    def mark_pending(self, request, queryset):
        queryset.update(delivery_status='pending')
        self.message_user(request, f'✅ تم التحديث')

    @action(description='📦 قيد التحضير')
    def mark_preparing(self, request, queryset):
        queryset.update(delivery_status='preparing')
        self.message_user(request, f'✅ تم التحديث')

    @action(description='🚚 قيد التوصيل')
    def mark_shipped(self, request, queryset):
        queryset.update(delivery_status='shipped')
        self.message_user(request, f'✅ تم التحديث')

    @action(description='✅ تم التوصيل')
    def mark_delivered(self, request, queryset):
        queryset.update(delivery_status='delivered')
        self.message_user(request, f'✅ تم التحديث')

    @action(description='↩️ مرتجع')
    def mark_returned(self, request, queryset):
        queryset.update(delivery_status='returned')
        self.message_user(request, f'✅ تم التحديث')

    @action(description='❌ لم يُدفع')
    def mark_unpaid(self, request, queryset):
        queryset.update(payment_status='unpaid')
        self.message_user(request, f'✅ تم التحديث')

    @action(description='💰 دفع جزئي')
    def mark_partial(self, request, queryset):
        queryset.update(payment_status='partial')
        self.message_user(request, f'✅ تم التحديث')

    @action(description='✅ تم الدفع')
    def mark_paid(self, request, queryset):
        queryset.update(payment_status='paid')
        self.message_user(request, f'✅ تم التحديث')

    @action(description='↩️ مسترد')
    def mark_refunded(self, request, queryset):
        queryset.update(payment_status='refunded')
        self.message_user(request, f'✅ تم التحديث')


@admin.register(InvoiceItem)
class InvoiceItemAdmin(ModelAdmin):
    list_display = ['invoice', 'product', 'quantity', 'unit_price']
    list_filter = ['invoice__delivery_status', 'invoice__payment_status']
    search_fields = ['invoice__invoice_number', 'product__title']
    autocomplete_fields = ['invoice', 'product']


admin.site.site_header = "SB by Sabah — لوحة التحكم"
admin.site.site_title = "SB by Sabah"
admin.site.index_title = "لوحة التحكم ✨"
