# apps/leads/apps.py — конфигурация приложения заявок
from django.apps import AppConfig


class LeadsConfig(AppConfig):
    """Заявки с форм сайта и уведомления о них."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.leads"
    verbose_name = "Заявки"
