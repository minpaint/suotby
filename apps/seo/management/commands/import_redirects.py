# apps/seo/management/commands/import_redirects.py — переадресации и 410 из redirects.csv
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from apps.seo.legacy_csv import read_rows
from apps.seo.models import Gone, Redirect
from apps.seo.services import reset_maps


class Command(BaseCommand):
    help = "Загружает точные 301 и 410 из docs/data/redirects.csv (правила с * реализованы в middleware)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--csv", default="docs/data/redirects.csv")

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        path = Path(options["csv"])
        if not path.is_file():
            raise CommandError(f"Нет файла {path}")
        n301 = n410 = 0
        patterns: list[str] = []
        for row in read_rows(path):
            if row.action not in {"301", "410"}:
                continue
            if row.is_pattern:
                patterns.append(row.old_path)
                continue
            if row.action == "301":
                Redirect.objects.update_or_create(
                    old_path=row.old_path,
                    defaults={"new_path": row.new_path, "code": 301, "note": row.note},
                )
                n301 += 1
            else:
                Gone.objects.update_or_create(path=row.old_path, defaults={"note": row.note})
                n410 += 1
        reset_maps()
        self.stdout.write(f"301: {n301}, 410: {n410}")
        self.stdout.write("Правила с * (обрабатываются в apps/seo/services.py и Nginx):")
        for p in patterns:
            self.stdout.write(f"  — {p}")
        self.stdout.write(self.style.SUCCESS("Готово"))
