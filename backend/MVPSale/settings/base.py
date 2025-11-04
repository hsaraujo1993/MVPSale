import os
from datetime import timedelta


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure logs directory exists for file handlers
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "corsheaders",

    # Local apps
    "core",
    "api",
    "catalog",
    "people",
    "stock",
    "purchase",
    "sale",
    "payment",
    "nfe",
    "cashier",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "MVPSale.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            # Novo Front templates (repo root sibling of backend)
            os.path.join(os.path.dirname(BASE_DIR), "Novo Front", "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "MVPSale.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DJANGO_DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DJANGO_DB_NAME", os.path.join(BASE_DIR, "db.sqlite3")),
        "USER": os.getenv("DJANGO_DB_USER", ""),
        "PASSWORD": os.getenv("DJANGO_DB_PASSWORD", ""),
        "HOST": os.getenv("DJANGO_DB_HOST", ""),
        "PORT": os.getenv("DJANGO_DB_PORT", ""),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = os.getenv("TZ", "America/Sao_Paulo")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [
    # Novo Front static assets (repo root sibling of backend)
    os.path.join(os.path.dirname(BASE_DIR), "Novo Front", "static"),
]

# CORS
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL", "1") == "1"
CORS_ALLOWED_ORIGINS = [o for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o]

# DRF
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": int(os.getenv("DRF_PAGE_SIZE", "20")),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "MVPSale API",
    "DESCRIPTION": "API do sistema de vendas",
    "VERSION": "1.0.0",
    "SERVERS": [
        {"url": "/api", "description": "API base"},
    ],
}

# SimpleJWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MIN", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": os.getenv("JWT_ROTATE", "0") == "1",
    "BLACKLIST_AFTER_ROTATION": os.getenv("JWT_BLACKLIST", "0") == "1",
}

# Auth redirects
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

# Business rules configuration
MIN_MARGIN_PERCENT = float(os.getenv("MIN_MARGIN_PERCENT", "0"))
PREVENT_NEGATIVE_STOCK = os.getenv("PREVENT_NEGATIVE_STOCK", "1") == "1"
BLOCK_SALE_IF_ZERO_STOCK = os.getenv("BLOCK_SALE_IF_ZERO_STOCK", "1") == "1"
CASHIER_REQUIRED_FOR_SALE = os.getenv("CASHIER_REQUIRED_FOR_SALE", "1") == "1"

# Webmania CEP integration
WEBMANIA_APP_KEY = os.getenv("WEBMANIA_APP_KEY", "")
WEBMANIA_APP_SECRET = os.getenv("WEBMANIA_APP_SECRET", "")
WEBMANIA_CEP_ENABLED = os.getenv("WEBMANIA_CEP_ENABLED", "1") == "1"

# Logging configuration (file + console). Purchase service writes to 'purchase' logger.
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "level": LOG_LEVEL,
        },
        "purchase_file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "purchase.log"),
            "formatter": "verbose",
            "level": "INFO",
            "encoding": "utf-8",
        },
        "payment_file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "payment.log"),
            "formatter": "verbose",
            "level": "INFO",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "purchase": {
            "handlers": ["console", "purchase_file"],
            "level": "INFO",
            "propagate": False,
        },
        "purchase.services.nfe_import": {
            "handlers": ["console", "purchase_file"],
            "level": "INFO",
            "propagate": False,
        },
        "payment": {
            "handlers": ["console", "payment_file"],
            "level": "INFO",
            "propagate": False,
        },
        "sale.payment": {
            "handlers": ["console", "payment_file"],
            "level": "INFO",
            "propagate": False,
        },
        "nfe": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Focus NFe configuration (fill later)
FOCUSNFE_API_TOKEN = os.getenv("FOCUSNFE_API_TOKEN", "")
FOCUSNFE_BASE_URL = os.getenv("FOCUSNFE_BASE_URL", "https://homologacao.focusnfe.com.br")
