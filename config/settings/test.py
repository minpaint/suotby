# config/settings/test.py — настройки для pytest и CI
"""Тесты: быстрый хешер паролей, письма в память, изолированные папки медиа."""

import tempfile
from pathlib import Path

from .base import *  # noqa: F403
from .base import env

DEBUG = False
SECRET_KEY = "test-only-key"  # noqa: S105  # nosec B105
ALLOWED_HOSTS = ["testserver", "localhost", "suot.by", "www.suot.by"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
LEADS_NOTIFY_EMAILS = ["leads@example.com"]
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
_tmp = Path(tempfile.mkdtemp(prefix="suot-test-"))
MEDIA_ROOT = _tmp / "media"
PRIVATE_MEDIA_ROOT = _tmp / "private"
STATIC_ROOT = _tmp / "static"
STATIC_ROOT.mkdir(parents=True, exist_ok=True)
DATABASES = {"default": env.db("DATABASE_URL", default="postgres://suot:suot@localhost:5432/suot")}
TELEGRAM_BOT_TOKEN = ""  # nosec B105
