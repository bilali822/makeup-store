from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    """مستخدم مخصص - ممكن يكون بائع أو مشتري أو التنين"""
    is_seller = models.BooleanField(default=False, verbose_name="بائع")
    phone = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")
    address = models.TextField(blank=True, verbose_name="العنوان")

    def __str__(self):
        return self.username


class Category(models.Model):
    """فئة المنتج: مكياج، عطور، عناية..."""
    name = models.CharField(max_length=100, verbose_name="اسم الفئة")
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, default='fa-spa', verbose_name='الأيقونة')

    class Meta:
        verbose_name = "فئة"
        verbose_name_plural = "الفئات"

    def __str__(self):
        return self.name


class Product(models.Model):
    """المنتج - كل منتج له مالك (البائع)"""
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="البائع"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="الفئة"
    )
    title = models.CharField(max_length=200, verbose_name="اسم المنتج")
    description = models.TextField(blank=True, verbose_name="الوصف")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="الصورة")
    image_url = models.URLField(blank=True, null=True, verbose_name="رابط الصورة")
    stock = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    is_active = models.BooleanField(default=True, verbose_name="متاح")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "منتج"
        verbose_name_plural = "المنتجات"
        ordering = ['-created_at']

    @property
    def display_image(self):
        """إرجاع رابط الصورة — image_url أولاً، ثم image"""
        if self.image_url:
            return self.image_url
        if self.image:
            try:
                return self.image.url
            except Exception:
                return None
        return None

    def __str__(self):
        return self.title


class Order(models.Model):
    """الطلب - المشتري + المنتج + الحالة"""
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('confirmed', 'مؤكد'),
        ('shipped', 'تم الشحن'),
        ('delivered', 'تم التسليم'),
        ('cancelled', 'ملغى'),
    ]

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name="المشتري"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="المنتج")
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="الحالة")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"

    def __str__(self):
        return f"طلب #{self.id} - {self.product.title}"

    @property
    def total(self):
        return self.product.price * self.quantity



# ═══════════════════════════════════════════
# CUSTOMER (Proxy لعرض العملاء فقط)
# ═══════════════════════════════════════════
class Customer(User):
    """واجهة لعرض العملاء (المشترين) فقط"""
    class Meta:
        proxy = True
        verbose_name = "عميل"
        verbose_name_plural = "العملاء"


# ═══════════════════════════════════════════
# INVOICE
# ═══════════════════════════════════════════
class Invoice(models.Model):
    """الفاتورة — تصدر لكل طلب"""
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('sent', 'مُرسلة'),
        ('paid', 'مدفوعة'),
        ('overdue', 'متأخرة'),
        ('cancelled', 'ملغاة'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True, verbose_name="رقم الفاتورة", blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='invoices', verbose_name="الطلب")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invoices', verbose_name="العميل")
    issue_date = models.DateField(default=timezone.now, verbose_name="تاريخ الإصدار")
    due_date = models.DateField(null=True, blank=True, verbose_name="تاريخ الاستحقاق")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="المجموع الفرعي")
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الضريبة")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الخصم")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الإجمالي")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="الحالة")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "فاتورة"
        verbose_name_plural = "الفواتير"
        ordering = ['-created_at']

    def __str__(self):
        return f"فاتورة {self.invoice_number}"

    def save(self, *args, **kwargs):
        # توليد رقم الفاتورة تلقائياً
        if not self.invoice_number:
            last = Invoice.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.invoice_number = f"INV-{timezone.now().strftime('%Y%m')}-{next_id:04d}"

        # حساب المبالغ تلقائياً من الطلب
        if self.order:
            if not self.subtotal:
                self.subtotal = self.order.total
            self.total = self.subtotal + (self.tax or 0) - (self.discount or 0)

        super().save(*args, **kwargs)
