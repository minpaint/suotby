# config/settings/base.py — общие настройки для всех окружений
"""
Базовые настройки suot.by.

Все секреты и зависящие от окружения значения читаются из переменных окружения / файла `.env`
через django-environ. Шаблон — `.env.example` в корне репозитория.
"""

from pathlib import Path
from typing import Any

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
)
# 💡 .env читается, только если он есть: на сервере переменные обычно задаёт systemd
environ.Env.read_env(BASE_DIR / ".env", overwrite=False)

# 🔐 SECRET_KEY обязан приходить из окружения; в dev/test задаётся своё значение по умолчанию
SECRET_KEY = env("SECRET_KEY", default="")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

# Канонический адрес сайта — для canonical, sitemap, Open Graph, писем
SITE_URL = env("SITE_URL", default="https://suot.by").rstrip("/")
# Хост, на который сводятся www и прочие зеркала (правило хоста из redirects.csv)
CANONICAL_HOST = env("CANONICAL_HOST", default="suot.by")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.postgres",
    "django_ckeditor_5",
    "apps.core",
    "apps.content",
    "apps.leads",
    "apps.seo",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # ⚠️ переадресации со старого сайта — до сессий и CSRF: им не нужен ни пользователь, ни сессия
    "apps.seo.middleware.LegacyRedirectMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
]

# ⚠️ Старые адреса плоские и без завершающего слеша (`/slug.html`): автодобавление слеша
# сломало бы их и породило лишние 301
APPEND_SLASH = False

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# База: PostgreSQL по DATABASE_URL (для быстрых экспериментов допустим sqlite:///db.sqlite3)
DATABASES = {"default": env.db("DATABASE_URL", default="postgres://suot:suot@localhost:5432/suot")}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Minsk"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------- статика и медиа
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

MEDIA_URL = "/media/"
MEDIA_ROOT = Path(env("MEDIA_ROOT", default=str(BASE_DIR / "media")))
# 🔐 Вложения заявок — вне публичного MEDIA_ROOT, отдаются только сотрудникам через админку
PRIVATE_MEDIA_ROOT = Path(env("PRIVATE_MEDIA_ROOT", default=str(BASE_DIR / "private_media")))

# Максимальный размер файла в заявке (байт)
LEAD_ATTACHMENT_MAX_SIZE = env.int("LEAD_ATTACHMENT_MAX_SIZE", default=10 * 1024 * 1024)
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# ---------------------------------------------------------------- админка
# 🔐 Неочевидный адрес админки (задаётся в .env), чтобы не светить /admin/ ботам
ADMIN_URL = env("ADMIN_URL", default="upravlenie/").strip("/") + "/"

# ---------------------------------------------------------------- почта и уведомления о заявках
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="СУОТ.BY <noreply@suot.by>")
# Кому уходят заявки (через запятую)
LEADS_NOTIFY_EMAILS = env.list("LEADS_NOTIFY_EMAILS", default=[])
# 💡 Telegram-уведомления включаются, если заданы оба значения
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_CHAT_ID = env("TELEGRAM_CHAT_ID", default="")

# ---------------------------------------------------------------- кэш
CACHES = {"default": env.cache("CACHE_URL", default="locmemcache://suot")}
# Время жизни кэша страниц разделов и главной (сек.)
PAGE_CACHE_SECONDS = env.int("PAGE_CACHE_SECONDS", default=300)

# ---------------------------------------------------------------- лимиты частоты (django-ratelimit)
RATELIMIT_USE_CACHE = "default"
LEAD_RATE = env("LEAD_RATE", default="5/h")

# ---------------------------------------------------------------- безопасность
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # ⚠️ форма отправляется обычным POST, токен берётся из шаблона
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# 🔐 CSP: свои ресурсы + Google Fonts + YouTube (превью и ссылки) + Яндекс.Метрика
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        # ⚠️ 'unsafe-inline' только для стилей: в шаблонах есть style-атрибуты; скрипты остаются под запретом
        "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        "font-src": ["'self'", "https://fonts.gstatic.com"],
        "img-src": ["'self'", "data:", "https://i.ytimg.com", "https://mc.yandex.ru"],
        "script-src": ["'self'", "https://mc.yandex.ru"],
        "connect-src": ["'self'", "https://mc.yandex.ru"],
        "frame-ancestors": ["'none'"],
        "form-action": ["'self'"],
        "base-uri": ["'self'"],
    }
}

# Счётчик Яндекс.Метрики (номер), пусто — счётчик не выводится
YANDEX_METRIKA_ID = env("YANDEX_METRIKA_ID", default="")

# ---------------------------------------------------------------- CKEditor 5
CKEDITOR_5_UPLOAD_PATH = "uploads/"
CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"
CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": {
            "items": [
                "heading",
                "|",
                "bold",
                "italic",
                "link",
                "bulletedList",
                "numberedList",
                "blockQuote",
                "|",
                "insertTable",
                "imageUpload",
                "|",
                "undo",
                "redo",
                "sourceEditing",
            ]
        },
        "heading": {
            "options": [
                {"model": "paragraph", "title": "Абзац", "class": "ck-heading_paragraph"},
                {
                    "model": "heading2",
                    "view": "h2",
                    "title": "Заголовок 2",
                    "class": "ck-heading_heading2",
                },
                {
                    "model": "heading3",
                    "view": "h3",
                    "title": "Заголовок 3",
                    "class": "ck-heading_heading3",
                },
                {
                    "model": "heading4",
                    "view": "h4",
                    "title": "Заголовок 4",
                    "class": "ck-heading_heading4",
                },
            ]
        },
        "table": {"contentToolbar": ["tableColumn", "tableRow", "mergeTableCells"]},
    }
}

# ---------------------------------------------------------------- логирование
LOG_LEVEL = env("LOG_LEVEL", default="INFO")
LOGGING: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "default"},
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING"},
        "apps": {"handlers": ["console"], "level": LOG_LEVEL},
        # 🔐 отдельный журнал безопасности/аудита: заявки, отказы форм, превышения лимитов
        "security": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# ---------------------------------------------------------------- Sentry (необязательно)
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:  # pragma: no cover — включается только на сервере
    import sentry_sdk

    sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1, send_default_pii=False)
