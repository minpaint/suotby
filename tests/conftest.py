# tests/conftest.py — общие фикстуры pytest
from __future__ import annotations

from pathlib import Path

import pytest
from django.core.cache import cache
from django.test import Client

from apps.content.importer import JoomlaImporter
from apps.content.seed import seed_all

FIXTURES = Path(__file__).parent / "fixtures"
EXPORT = FIXTURES / "export"


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """Каждый тест — с пустым кэшем (настройки сайта, таблицы переадресаций, лимиты)."""
    cache.clear()


@pytest.fixture
def seeded(db: None) -> None:
    """Сайт со структурой разделов, служебными страницами, клиентами и ценами."""
    seed_all()


@pytest.fixture
def imported(seeded: None) -> JoomlaImporter:
    """Сайт с импортированными образцами выгрузки (tests/fixtures/export)."""
    importer = JoomlaImporter(EXPORT)
    importer.run()
    return importer


@pytest.fixture
def client() -> Client:
    return Client(HTTP_HOST="suot.by")
