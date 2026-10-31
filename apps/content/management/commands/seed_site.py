# apps/content/management/commands/seed_site.py — начальное заполнение сайта
from typing import Any

from django.core.management.base import BaseCommand

from apps.content.seed import seed_all


class Command(BaseCommand):
    help = (
        "Создаёт разделы, служебные страницы, клиентов и позиции цен (повторный запуск безопасен)."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        result = seed_all()
        self.stdout.write(
            self.style.SUCCESS("Готово: " + ", ".join(f"{k}={v}" for k, v in result.items()))
        )
