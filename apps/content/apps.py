# apps/content/apps.py — конфигурация приложения content
from django.apps import AppConfig


class ContentConfig(AppConfig):
    """Разделы и материалы сайта: услуги, статьи, образцы, вопрос-ответ."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.content"
    verbose_name = "Контент"
