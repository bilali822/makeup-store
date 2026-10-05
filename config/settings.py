"""
Django settings for makeup_store project.
Render-ready configuration.
"""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ═══════════════════════════════════════════
# SECURITY
# ═══════════════════════════════════════════
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-only-insecure-key-change-in-production",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get(
        "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1"
    ).split(",")
    if h.strip()
]

RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# ═══════════════════════════════════════════
# APPLICATIONS
# ═══════════════════════════════════════════
INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "store",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "store" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ═══════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ═══════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "store.User"

# ═══════════════════════════════════════════
# I18N
# ═══════════════════════════════════════════
LANGUAGE_CODE = "ar"
TIME_ZONE = "Asia/Beirut"
USE_I18N = True
USE_TZ = True

# ═══════════════════════════════════════════
# STATIC & MEDIA
# ═══════════════════════════════════════════
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# ═══════════════════════════════════════════
# EMAIL
# ═══════════════════════════════════════════
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ═══════════════════════════════════════════
# DEFAULT PK
# ═══════════════════════════════════════════
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ═══════════════════════════════════════════
# PRODUCTION SECURITY
# ═══════════════════════════════════════════
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# ═══════════════════════════════════════════
# IMGBB — Image Hosting
# ═══════════════════════════════════════════
IMGBB_API_KEY = os.environ.get('IMGBB_API_KEY', '')






# ═══════════════════════════════════════════
# LOGGING (لتشخيص الأخطاء)
# ═══════════════════════════════════════════
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# ═══════════════════════════════════════════
# UNFOLD — لوحة تحكم عصرية
# ═══════════════════════════════════════════
from django.urls import reverse_lazy

UNFOLD = {
    "SITE_TITLE": "SB by Sabah — لوحة التحكم",
    "SITE_HEADER": "SB by Sabah",
    "SITE_URL": "/",
    "SITE_SYMBOL": "spa",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON": True,
    "DASHBOARD_CALLBACK": "store.admin.dashboard_callback",
    "THEME": "light",
    "LOGIN": {
        "image": None,
        "redirect_after": None,
    },
    "STYLES": [],
    "SCRIPTS": [],
    "COLORS": {
        "primary": {
            "50": "250 245 250",
            "100": "252 231 243",
            "200": "251 207 232",
            "300": "249 168 212",
            "400": "244 114 182",
            "500": "236 72 153",
            "600": "219 39 119",
            "700": "190 24 93",
            "800": "157 23 77",
            "900": "131 24 67",
            "950": "80 7 36",
        },
    },
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "ar": "🇱🇧",
            },
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "الرئيسية",
                "separator": False,
                "items": [
                    {
                        "title": "لوحة التحكم",
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": "المتجر",
                "separator": True,
                "items": [
                    {
                        "title": "المنتجات",
                        "icon": "spa",
                        "link": reverse_lazy("admin:store_product_changelist"),
                    },
                    {
                        "title": "الفئات",
                        "icon": "category",
                        "link": reverse_lazy("admin:store_category_changelist"),
                    },
                    {
                        "title": "الطلبات",
                        "icon": "shopping_bag",
                        "link": reverse_lazy("admin:store_order_changelist"),
                    },
                ],
            },
            {
                "title": "المبيعات",
                "separator": True,
                "items": [
                    {
                        "title": "الفواتير",
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:store_invoice_changelist"),
                    },
                ],
            },
            {
                "title": "العملاء",
                "separator": True,
                "items": [
                    {
                        "title": "العملاء",
                        "icon": "person",
                        "link": reverse_lazy("admin:store_customer_changelist"),
                    },
                ],
            },
            {
                "title": "الإدارة",
                "separator": True,
                "items": [
                    {
                        "title": "المستخدمون",
                        "icon": "admin_panel_settings",
                        "link": reverse_lazy("admin:store_user_changelist"),
                    },
                    {
                        "title": "المجموعات",
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
        ],
    },
}
