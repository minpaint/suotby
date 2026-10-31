# tests/test_import.py — импорт выгрузки Joomla на образцах
from pathlib import Path

import pytest
from django.core.management import call_command

from apps.content.importer import JoomlaImporter, clean_body, normalize_path
from apps.content.models import Category, Material
from tests.conftest import EXPORT

pytestmark = pytest.mark.django_db


def test_import_counts_and_types(imported: JoomlaImporter) -> None:
    r = imported.report
    assert r.created + r.updated == 9
    assert any("id 40" in s for s in r.skipped)
    assert Material.objects.get(legacy_id="151").type == Material.Type.REQUIREMENT
    assert Material.objects.get(legacy_id="184").type == Material.Type.FAQ
    assert Material.objects.get(legacy_id="106").type == Material.Type.ORDER_SAMPLE
    assert not Material.objects.filter(legacy_id="46").exists()  # корзина


def test_import_keeps_old_paths_and_fixes_broken_dash(imported: JoomlaImporter) -> None:
    assert Material.objects.filter(
        path="/obsluzhivanie-organizacii-v-kachestve-specialista-po-ohrane-truda.html"
    ).exists()
    assert Material.objects.filter(
        path="/razrabotka-sistemy-upravleniya-ohranoj-truda-eto-obyazatelno.html"
    ).exists()
    assert imported.report.fixed_paths


def test_import_categories(imported: JoomlaImporter) -> None:
    assert (
        Material.objects.get(legacy_id="184").category.slug == "organizaciya-raboty-po-ohrane-truda"
    )
    assert Material.objects.get(legacy_id="75").category.kind == Category.Kind.SERVICES_SUOT
    assert Material.objects.get(legacy_id="71").category.kind == Category.Kind.SERVICES_OT
    assert Material.objects.get(legacy_id="106").category.slug == "prikazy-po-ohrane-truda"


@pytest.mark.parametrize("separator", ["/", "\\"])
@pytest.mark.parametrize(
    ("folder", "slug"),
    [("stati", "stati"), ("prikazy", "prikazy-po-ohrane-truda")],
)
def test_category_for_native_paths(seeded: None, separator: str, folder: str, slug: str) -> None:
    importer = JoomlaImporter(EXPORT)
    category = importer.category_for({}, f"{folder}{separator}example.md")
    assert category is not None
    assert category.slug == slug


def test_import_sanitizes_and_cleans_junk(imported: JoomlaImporter) -> None:
    faq = Material.objects.get(legacy_id="184")
    assert "<script" not in faq.body
    order = Material.objects.get(legacy_id="106")
    assert "onclick" not in order.body
    assert "Представляем" in order.intro and "ПРИКАЗ" in order.body
    service = Material.objects.get(legacy_id="71")
    assert "ОТПРАВИТЬ ЗАЯВКУ" not in service.body
    assert "Оставьте заявку" not in service.body
    assert "consult.png" not in service.body
    assert 'alt=""' in service.body
    assert "{loadposition" not in Material.objects.get(legacy_id="310").body


def test_import_rewrites_media_and_self_links(imported: JoomlaImporter) -> None:
    page = Material.objects.get(legacy_id="45")
    assert "/media/legacy/images/razrabotka.png" in page.body
    article = Material.objects.get(legacy_id="96")
    assert article.cover.name == "legacy/images/spec.jpg"
    assert (
        'href="/obsluzhivanie-organizacii-v-kachestve-specialista-po-ohrane-truda.html"'
        in article.body
    )
    assert "images/2021/11/14/obslugivanie-po-ohrane-truda.jpg" in imported.report.missing_media


def test_import_special_page_merges_with_seeded(imported: JoomlaImporter) -> None:
    prices = Material.objects.get(path="/ceny-na-razrabotku-suot-v-minske.html")
    assert prices.legacy_id == "47"
    assert prices.template == Material.Template.PRICES
    assert Material.objects.filter(path="/ceny-na-razrabotku-suot-v-minske.html").count() == 1


def test_import_is_idempotent(imported: JoomlaImporter) -> None:
    before = Material.objects.count()
    report = JoomlaImporter(EXPORT).run()
    assert Material.objects.count() == before
    assert report.created == 0


def test_import_command_and_report(seeded: None, tmp_path: Path) -> None:
    report = tmp_path / "r.txt"
    call_command("import_joomla", source=str(EXPORT), no_media=True, report=str(report))
    assert "Создано материалов" in report.read_text(encoding="utf-8")


def test_import_command_missing_dir(db: None) -> None:
    from django.core.management.base import CommandError

    with pytest.raises(CommandError):
        call_command("import_joomla", source="/nonexistent")


def test_organization_service_classification(seeded: None) -> None:
    """Услуга из Uncategorised остаётся услугой после повторного импорта."""
    importer = JoomlaImporter(EXPORT)
    meta = {
        "id": 34,
        "title": "Организация работы по охране труда в организации",
        "url": "/kachestvennaya-razrabotka-dokumentov-po-ohrane-truda-individualno-dlya-vashej-organizacii.html",
        "type": "страница",
        "category": "Uncategorised",
    }
    for _ in range(2):
        importer.import_material(meta, "Организуем работу по охране труда.", "stranicy/34.md")
    material = Material.objects.get(legacy_id="34")
    assert material.type == Material.Type.SERVICE
    assert material.category.kind == Category.Kind.SERVICES_OT


def test_helpers() -> None:
    assert normalize_path("/a-b.html") == "/a-b.html"
    assert normalize_path("/a-–-b.html") == "/a-b.html"
    assert "ok" in clean_body("ok\n\nButton Text\n{sh404sef}", strip_cta=False)
    assert "Button" not in clean_body("ok\nButton Text", strip_cta=False)
    assert clean_body("текст\n### Бесплатная консультация\n+375", strip_cta=True) == "текст"
