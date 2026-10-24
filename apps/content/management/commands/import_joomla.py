# apps/content/management/commands/import_joomla.py — импорт выгрузки старого сайта
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.content.importer import JoomlaImporter
from apps.content.seed import seed_all


class Command(BaseCommand):
    help = "Импортирует выгрузку Joomla (папка content с .md и _media). Повторный запуск обновляет материалы."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--source", default="data/content", help="папка выгрузки (по умолчанию data/content)"
        )
        parser.add_argument(
            "--no-media", action="store_true", help="не копировать картинки из _media"
        )
        parser.add_argument("--report", help="записать отчёт в файл")

    def handle(self, *args: Any, **options: Any) -> None:
        source = Path(options["source"])
        if not source.is_dir():
            raise CommandError(
                f"Нет папки {source}. Скопируйте выгрузку с Google Диска (coding/suot.by/content)."
            )
        seed_all()  # структура разделов нужна до привязки материалов
        report = JoomlaImporter(source, copy_media=not options["no_media"]).run()
        text = "\n".join(report.lines())
        self.stdout.write(text)
        if options.get("report"):
            Path(options["report"]).write_text(text, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS("Импорт завершён"))
