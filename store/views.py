from django.shortcuts import render, get_object_or_404
from .models import Product, Category


def home(request):
    """الصفحة الرئيسية - كل المنتجات + الفئات"""
    products = Product.objects.filter(is_active=True).select_related('category', 'owner')
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'store/home.html', context)


def product_detail(request, product_id):
    """صفحة تفاصيل منتج واحد"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    context = {
        'product': product,
    }
    return render(request, 'store/product_detail.html', context)


def category_detail(request, slug):
    """صفحة فئة معينة - تعرض كل منتجات هالفئة"""
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(
        category=category, 
        is_active=True
    ).select_related('owner')
    categories = Category.objects.all()
    
    context = {
        'category': category,
        'products': products,
        'categories': categories,
    }
    return render(request, 'store/category.html', context)
