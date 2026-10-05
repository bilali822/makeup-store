from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


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
