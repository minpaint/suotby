# apps/core/apps.py — конфигурация приложения core
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Общие вещи сайта: настройки, главная, шапка/подвал, санитайзер."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Сайт"
