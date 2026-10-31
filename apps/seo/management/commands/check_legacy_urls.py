# apps/seo/management/commands/check_legacy_urls.py — главный тест переезда: все старые адреса живы
"""
Проходит по redirects.csv и проверяет каждый адрес тестовым клиентом Django:

* ``keep`` → 200;
* ``301`` → 301 на указанный адрес;
* ``410`` → 410.

Код выхода 1, если есть ошибки (удобно для CI и проверки перед переключением DNS).
"""

from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from django.test import Client

from apps.seo.legacy_csv import read_rows


class Command(BaseCommand):
    help = "Проверяет, что все адреса из redirects.csv отвечают как задумано (keep=200, 301, 410)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--csv", default="docs/data/redirects.csv")
        parser.add_argument(
            "--only", choices=["keep", "301", "410"], help="проверить только один вид"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        host = next(
            (h for h in settings.ALLOWED_HOSTS if h and not h.startswith(".") and h != "*"),
            "localhost",
        )
        client = Client(HTTP_HOST=host)
        failures: list[str] = []
        checked = 0
        for row in read_rows(Path(options["csv"])):
            if row.is_pattern or row.action not in {"keep", "301", "410"}:
                continue
            if options.get("only") and row.action != options["only"]:
                continue
            checked += 1
            resp = client.get(row.old_path)
            if row.action == "keep" and resp.status_code != 200:
                failures.append(f"keep {row.old_path}: {resp.status_code}")
            elif row.action == "301":
                location = resp.headers.get("Location", "")
                if resp.status_code != 301 or location.split("?")[0] != row.new_path:
                    failures.append(
                        f"301 {row.old_path}: {resp.status_code} → {location or '—'} (ждали {row.new_path})"
                    )
            elif row.action == "410" and resp.status_code != 410:
                failures.append(f"410 {row.old_path}: {resp.status_code}")
        for f in failures:
            self.stdout.write(self.style.ERROR(f))
        summary = f"Проверено: {checked}, ошибок: {len(failures)}"
        if failures:
            self.stdout.write(self.style.ERROR(summary))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS(summary))
