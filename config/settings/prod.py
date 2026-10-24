# config/settings/prod.py — боевые настройки (Gunicorn за Nginx)
"""Прод: обязательный SECRET_KEY, HTTPS, HSTS, защищённые cookie."""

from typing import Any

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import LOGGING, SECRET_KEY, env

if not SECRET_KEY:
    raise ImproperlyConfigured("🔐 Задайте SECRET_KEY в окружении")

DEBUG = False
# Nginx терминирует TLS и передаёт схему в заголовке
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False

_handlers: dict[str, Any] = LOGGING["handlers"]
_loggers: dict[str, Any] = LOGGING["loggers"]
_handlers["file"] = {
    "class": "logging.handlers.RotatingFileHandler",
    "filename": env("LOG_FILE", default="/var/log/suotby/app.log"),
    "maxBytes": 10 * 1024 * 1024,
    "backupCount": 5,
    "formatter": "default",
}
_handlers["security_file"] = {
    "class": "logging.handlers.RotatingFileHandler",
    "filename": env("SECURITY_LOG_FILE", default="/var/log/suotby/security.log"),
    "maxBytes": 10 * 1024 * 1024,
    "backupCount": 10,
    "formatter": "default",
}
_loggers["apps"]["handlers"] = ["console", "file"]
_loggers["security"]["handlers"] = ["console", "security_file"]
