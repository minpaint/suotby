# config/settings/dev.py — настройки локальной разработки
"""Разработка: DEBUG, письма в консоль, простой ключ по умолчанию."""

from .base import *  # noqa: F403
from .base import env

DEBUG = env.bool("DEBUG", default=True)
# 🔐 ключ только для разработки — на сервере обязателен свой SECRET_KEY
SECRET_KEY = env("SECRET_KEY", default="dev-only-insecure-key-change-me")
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
