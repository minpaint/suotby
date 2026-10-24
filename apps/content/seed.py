# apps/content/seed.py — создание структуры сайта (разделы, служебные страницы, клиенты, цены)
"""
Идемпотентное заполнение: повторный запуск ничего не дублирует и не затирает правки из админки.
"""

from __future__ import annotations

from django.db import transaction

from apps.content import structure
from apps.content.models import Category, Material, PriceItem
from apps.content.services import SPECIAL_PAGE_TEMPLATES
from apps.core.models import Client, SiteSettings


def _upsert_category(d: structure.CategoryDef, parent: Category | None = None) -> Category:
    """Создаёт раздел, если его нет (поиск по slug); существующий не меняет."""
    cat, created = Category.objects.get_or_create(
        slug=d["slug"],
        defaults={
            "title": d["title"],
            "menu_title": d.get("menu_title", ""),
            "path": d.get("path", f"/{d['slug']}/"),
            "kind": d.get("kind", Category.Kind.FAQ),
            "template": d.get("template", Category.Template.DEFAULT),
            "legacy_id": d.get("legacy_id", ""),
            "show_in_useful": d.get("show_in_useful", False),
            "ordering": d.get("ordering", 0),
            "parent": parent,
        },
    )
    if not created and d.get("legacy_id") and not cat.legacy_id:
        cat.legacy_id = d["legacy_id"]
        cat.save(update_fields=["legacy_id"])
    return cat


@transaction.atomic
def ensure_structure() -> dict[str, int]:
    """
    Создаёт разделы «Полезное», «Вопрос-ответ» с подразделами и группы услуг.

    Returns:
        Счётчики созданных объектов по видам.
    """
    before = Category.objects.count()
    for d in structure.USEFUL:
        _upsert_category(d)
    root = _upsert_category(structure.FAQ_ROOT)
    for i, d in enumerate(structure.FAQ_SECTIONS):
        _upsert_category({**d, "kind": Category.Kind.FAQ, "ordering": i}, parent=root)
    for d in structure.SERVICE_GROUPS:
        _upsert_category(d)
    return {"categories": Category.objects.count() - before}


@transaction.atomic
def ensure_pages() -> int:
    """Создаёт служебные страницы (контакты, цены, о нас…), если их ещё нет. Returns: сколько создано."""
    created = 0
    for path, title in structure.SPECIAL_PAGES.items():
        slug = path.strip("/").removesuffix(".html").split("/")[-1]
        _, was_created = Material.objects.get_or_create(
            path=path,
            defaults={
                "slug": slug,
                "title": title,
                "type": Material.Type.PAGE,
                "template": SPECIAL_PAGE_TEMPLATES[path],
            },
        )
        created += was_created
    return created


@transaction.atomic
def ensure_clients() -> int:
    """Заполняет список клиентов, если он пуст. Returns: сколько создано."""
    if Client.objects.exists():
        return 0
    featured = set(structure.CLIENTS_FEATURED)
    seen: set[str] = set()
    objs = []
    for i, name in enumerate(structure.CLIENTS):
        if name in seen:
            continue
        seen.add(name)
        objs.append(Client(name=name, is_featured=name in featured, ordering=i))
    Client.objects.bulk_create(objs)
    return len(objs)


@transaction.atomic
def ensure_prices() -> int:
    """
    Создаёт позиции цен БЕЗ сумм (суммы вносит владелец в админке, на сайте — «по запросу»).

    Returns:
        Сколько создано.
    """
    if PriceItem.objects.exists():
        return 0
    items = [
        PriceItem(
            kind=PriceItem.Kind.TARIFF,
            title="Документы по ОТ",
            ordering=1,
            show_on_home=True,
            description="Комплект обязательных документов под вашу организацию.",
        ),
        PriceItem(
            kind=PriceItem.Kind.TARIFF,
            title="Разработка и внедрение СУОТ",
            ordering=2,
            show_on_home=True,
            is_highlighted=True,
            badge="Спецпредложение",
            description="При разработке СУОТ проекты инструкций по охране труда для профессий и видов работ "
            "в объёме вашей организации — бесплатно.",
        ),
        PriceItem(
            kind=PriceItem.Kind.TARIFF,
            title="Обслуживание организации",
            unit="/мес",
            ordering=3,
            show_on_home=True,
            description="Функции специалиста по охране труда по договору обслуживания.",
        ),
        PriceItem(
            kind=PriceItem.Kind.ROW, title="Аудит охраны труда", unit="организация", ordering=1
        ),
        PriceItem(
            kind=PriceItem.Kind.ROW,
            title="Инструкция по охране труда",
            unit="1 инструкция",
            ordering=2,
        ),
        PriceItem(
            kind=PriceItem.Kind.ROW,
            title="Карта идентификации опасностей и оценки рисков",
            unit="1 профессия",
            ordering=3,
        ),
        PriceItem(
            kind=PriceItem.Kind.ROW, title="Приказы по охране труда", unit="комплект", ordering=4
        ),
        PriceItem(
            kind=PriceItem.Kind.ROW, title="Выполнение предписания", unit="предписание", ordering=5
        ),
        PriceItem(kind=PriceItem.Kind.ROW, title="Консультация", unit="1 час", ordering=6),
    ]
    PriceItem.objects.bulk_create(items)
    return len(items)


def seed_all() -> dict[str, int]:
    """Полное начальное заполнение. Returns: счётчики по видам."""
    SiteSettings.load()
    result = ensure_structure()
    result["pages"] = ensure_pages()
    result["clients"] = ensure_clients()
    result["prices"] = ensure_prices()
    return result
