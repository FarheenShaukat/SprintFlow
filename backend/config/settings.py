from datetime import timedelta
from pathlib import Path

import dj_database_url
from decouple import AutoConfig, Csv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
config = AutoConfig(search_path=ROOT_DIR)
IS_VERCEL = bool(config("VERCEL", default=""))

SECRET_KEY = config("DJANGO_SECRET_KEY", default="dev-only-change-me")
DEBUG = config("DJANGO_DEBUG", default=not IS_VERCEL, cast=bool)
ALLOWED_HOSTS = list(config("DJANGO_ALLOWED_HOSTS", default="*", cast=Csv()))
VERCEL_URL = config("VERCEL_URL", default="")
if VERCEL_URL:
    ALLOWED_HOSTS.extend([VERCEL_URL, f".{VERCEL_URL}"])
if ".vercel.app" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".vercel.app")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "django_filters",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "oauth2_provider",
    "apps.integrations",
    "apps.accounts",
    "apps.workspaces",
    "apps.projects",
    "apps.tasks",
    "apps.comments",
    "apps.attachments",
    "apps.activity",
    "apps.ai",
    "apps.sprintflow_ai",
    "apps.reports",
]

MIDDLEWARE = [
    "apps.core.middleware.ApiDatabaseErrorMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
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
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASE_URL = config("DATABASE_URL", default="")
if IS_VERCEL and not DATABASE_URL:
    raise ImproperlyConfigured("DATABASE_URL is required on Vercel. Set it to your Supabase PostgreSQL connection string.")

DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000",
    cast=Csv(),
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SprintFlow AI API",
    "DESCRIPTION": "Mini Jira API with AI task assistance, sprint health, and project reports.",
    "VERSION": "1.0.0",
}

OPENAI_API_KEY = config("OPENAI_API_KEY", default="")
OPENAI_MODEL = config("OPENAI_MODEL", default="gpt-4o-mini")
GROQ_API_KEY = config("GROQ_API_KEY", default="")
GROQ_MODEL = config("GROQ_MODEL", default="llama-3.3-70b-versatile")
GROQ_BASE_URL = config("GROQ_BASE_URL", default="https://api.groq.com/openai/v1")
SUPABASE_URL = config("SUPABASE_URL", default="")
SUPABASE_SERVICE_ROLE_KEY = config("SUPABASE_SERVICE_ROLE_KEY", default="")

EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="SprintFlow AI <noreply@sprintflow.ai>")
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:3000")

MCP_PUBLIC_URL = config("MCP_PUBLIC_URL", default="http://localhost:8000").rstrip("/")
CSRF_TRUSTED_ORIGINS = [MCP_PUBLIC_URL]
SESSION_COOKIE_SECURE = IS_VERCEL or not DEBUG
CSRF_COOKIE_SECURE = IS_VERCEL or not DEBUG
if IS_VERCEL:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
LOGIN_URL = "/oauth/login"
OAUTH2_PROVIDER = {
    "SCOPES": {"sprintflow": "Read and manage your SprintFlow projects, tasks and teams"},
    "DEFAULT_SCOPES": ["sprintflow"],
    "PKCE_REQUIRED": True,
    "ACCESS_TOKEN_EXPIRE_SECONDS": 3600,
    "REFRESH_TOKEN_EXPIRE_SECONDS": 60 * 60 * 24 * 30,
    "ROTATE_REFRESH_TOKEN": True,
    "REFRESH_TOKEN_REUSE_PROTECTION": True,
    "COMPLIANT_BCP_RFC9700_PKCE_METHOD": True,
    "ALLOWED_REDIRECT_URI_SCHEMES": ["https", "http"],
    "OAUTH2_VALIDATOR_CLASS": "apps.integrations.oauth.MCPOAuth2Validator",
    "DCR_ENABLED": True,
    "DCR_REGISTRATION_PERMISSION_CLASSES": ["oauth2_provider.dcr.AllowAllDCRPermission"],
    "OIDC_ISS_ENDPOINT": MCP_PUBLIC_URL,
    "OAUTH2_PROTECTED_RESOURCE_IDENTIFIER": f"{MCP_PUBLIC_URL}/mcp",
    "OAUTH2_PROTECTED_RESOURCE_AUTHORIZATION_SERVERS": [MCP_PUBLIC_URL],
    "OAUTH2_RESPONSE_TYPES_SUPPORTED": ["code"],
    "OAUTH2_GRANT_TYPES_SUPPORTED": ["authorization_code", "refresh_token"],
    "OAUTH2_TOKEN_ENDPOINT_AUTH_METHODS_SUPPORTED": ["none"],
}
