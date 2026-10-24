# tests/test_misc.py — сидинг, теги шаблонов, миграции, ошибки
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import RequestFactory

from apps.content.models import Category, Material, PriceItem
from apps.content.templatetags.content_tags import safe_html, with_toc
from apps.core.models import Client as ClientModel
from apps.core.templatetags.site_tags import json_ld, price_label, tel
from apps.core.views import server_error

pytestmark = pytest.mark.django_db


def test_seed_is_idempotent(db: None) -> None:
    call_command("seed_site")
    counts = (
        Category.objects.count(),
        Material.objects.count(),
        ClientModel.objects.count(),
        PriceItem.objects.count(),
    )
    call_command("seed_site")
    assert counts == (
        Category.objects.count(),
        Material.objects.count(),
        ClientModel.objects.count(),
        PriceItem.objects.count(),
    )
    assert Category.objects.filter(kind="faq", parent__isnull=False).count() == 13
    assert ClientModel.objects.filter(is_featured=True).count() == 7


def test_price_label() -> None:
    assert price_label(None) == "по запросу"
    assert price_label(Decimal("300.00"), "/мес") == "от 300 BYN/мес"
    assert price_label("от 500") == "от 500 BYN"
    assert price_label("по договорённости") == "по договорённости"
    assert price_label("100 BYN") == "100 BYN"


def test_tel_and_json_ld() -> None:
    assert tel("+375 33 357-09-11") == "tel:+375333570911"
    out = json_ld({"name": "</script><script>alert(1)"})
    assert "</script><script>" not in out.split('application/ld+json">', 1)[1][:-9]


def test_toc() -> None:
    res = with_toc("<h2>Что требует ТК</h2><p>x</p><h2>Что требует ТК</h2>")
    assert [a for a, _ in res["toc"]] == ["chto-trebuet-tk", "chto-trebuet-tk-2"]
    assert 'id="chto-trebuet-tk"' in res["html"]
    assert safe_html(None) == ""


def test_server_error_page() -> None:
    resp = server_error(RequestFactory().get("/"))
    assert resp.status_code == 500
    assert "Что-то пошло не так" in resp.content.decode()


@pytest.mark.django_db(transaction=True)
def test_migrations_roll_back_and_forward() -> None:
    """✅ Миграции откатываются и накатываются заново без ошибок."""
    executor = MigrationExecutor(connection)
    targets = [("leads", None), ("seo", None)]
    executor.migrate(targets)
    executor.loader.build_graph()
    executor.migrate(executor.loader.graph.leaf_nodes())
    tables = connection.introspection.table_names()
    assert "leads_lead" in tables and "seo_redirect" in tables
