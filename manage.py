#!/usr/bin/env python
# manage.py — точка входа management-команд Django
"""Запуск команд Django. По умолчанию — настройки разработки."""

import os
import sys


def main() -> None:
    """Выставляет модуль настроек и передаёт управление Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
