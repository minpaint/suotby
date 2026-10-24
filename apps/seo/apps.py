# apps/seo/apps.py — конфигурация приложения SEO
from django.apps import AppConfig


class SeoConfig(AppConfig):
    """Переадресации со старого сайта, 410, sitemap.xml, robots.txt."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.seo"
    verbose_name = "SEO и адреса"

    def ready(self) -> None:
        from apps.seo import signals  # noqa: F401 — подключение обработчиков сброса кэша
