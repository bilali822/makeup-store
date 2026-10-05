from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone


# ═══════════════════════════════════════════
# USER
# ═══════════════════════════════════════════
class User(AbstractUser):
    """مستخدم مخصص - ممكن يكون بائع أو مشتري أو التنين"""
    is_seller = models.BooleanField(default=False, verbose_name="بائع")
    phone = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")
    address = models.TextField(blank=True, verbose_name="العنوان")

    def __str__(self):
        return self.username


# ═══════════════════════════════════════════
# CUSTOMER (Proxy للعملاء فقط)
# ═══════════════════════════════════════════
class Customer(User):
    """واجهة لعرض العملاء (المشترين) فقط"""
    class Meta:
        proxy = True
        verbose_name = "عميل"
        verbose_name_plural = "العملاء"


# ═══════════════════════════════════════════
# CATEGORY
# ═══════════════════════════════════════════
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم الفئة")
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, default='fa-spa', verbose_name='الأيقونة')

    class Meta:
        verbose_name = "فئة"
        verbose_name_plural = "الفئات"

    def __str__(self):
        return self.name


# ═══════════════════════════════════════════
# PRODUCT
# ═══════════════════════════════════════════
class Product(models.Model):
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


# ═══════════════════════════════════════════
# ORDER
# ═══════════════════════════════════════════
class Order(models.Model):
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
# INVOICE (فاتورة مستقلة)
# ═══════════════════════════════════════════
class Invoice(models.Model):
    DELIVERY_STATUS = [
        ('pending', 'قيد المعالجة'),
        ('preparing', 'قيد التحضير'),
        ('shipped', 'قيد التوصيل'),
        ('delivered', 'تم التوصيل'),
        ('returned', 'مرتجع'),
    ]
    PAYMENT_STATUS = [
        ('unpaid', 'لم يتم الدفع'),
        ('partial', 'دفع جزئي'),
        ('paid', 'تم الدفع'),
        ('refunded', 'مسترد'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True, verbose_name="رقم الفاتورة", blank=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name="العميل"
    )
    issue_date = models.DateField(default=timezone.now, verbose_name="تاريخ الإصدار")
    delivery_date = models.DateField(null=True, blank=True, verbose_name="تاريخ التوصيل")
    delivery_status = models.CharField(
        max_length=20, choices=DELIVERY_STATUS, default='pending',
        verbose_name="حالة التوصيل"
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS, default='unpaid',
        verbose_name="حالة الدفع"
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="المجموع الفرعي")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الخصم")
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="رسوم التوصيل")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الإجمالي")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "فاتورة"
        verbose_name_plural = "الفواتير"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.username}"

    def recalculate(self, save=True):
        """إعادة حساب المجموع من العناصر"""
        self.subtotal = sum(item.line_total for item in self.items.all())
        self.total = self.subtotal + (self.delivery_fee or 0) - (self.discount or 0)
        if save:
            self.save(update_fields=['subtotal', 'total'])

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last = Invoice.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.invoice_number = f"INV-{timezone.now().strftime('%Y%m')}-{next_id:04d}"
        super().save(*args, **kwargs)


# ═══════════════════════════════════════════
# INVOICE ITEM (عنصر في الفاتورة)
# ═══════════════════════════════════════════
class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE,
        related_name='items', verbose_name="الفاتورة"
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT,
        verbose_name="المنتج"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="سعر الوحدة")

    class Meta:
        verbose_name = "عنصر الفاتورة"
        verbose_name_plural = "عناصر الفاتورة"

    def __str__(self):
        return f"{self.product.title} × {self.quantity}"

    @property
    def line_total(self):
        return (self.unit_price or 0) * (self.quantity or 0)

    def save(self, *args, **kwargs):
        # إذا ما حدد سعر الوحدة، ناخده من المنتج
        if not self.unit_price and self.product:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)
        # نحدّث الفاتورة بعد الحفظ
        self.invoice.recalculate()
