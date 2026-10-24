# apps/content/services.py — выборки и логика контента (модели держим тонкими)
"""Сервисные функции раздела «Контент»: выборки для страниц, поиск, хабы."""

from __future__ import annotations

from dataclasses import dataclass, field

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import connection
from django.db.models import Count, F, Q, QuerySet

from apps.content.models import Category, Material

# ⚠️ Служебные страницы старого сайта, у которых на новом сайте свой шаблон.
# Ключ — старый адрес (не менять!), значение — шаблон из Material.Template.
SPECIAL_PAGE_TEMPLATES: dict[str, str] = {
    "/uslugi-po-ohrane-truda-v-minske-i-po-belarusi.html": Material.Template.SERVICES_HUB,
    "/pages/more-pages/vse-uslugi-po-suot.html": Material.Template.SERVICES_HUB,
    "/ceny-na-razrabotku-suot-v-minske.html": Material.Template.PRICES,
    "/kontakty.html": Material.Template.CONTACTS,
    "/o-nas.html": Material.Template.ABOUT,
    "/nashi-klienty.html": Material.Template.CLIENTS,
    "/usloviya-okazaniya-uslug.html": Material.Template.TERMS,
    "/karta-sajta.html": Material.Template.SITEMAP,
}

FAQ_HUB_PATH = "/chasto-zadavaemye-voprosy-po-ohrane-truda/"

# Шаблон по типу материала (если у материала template=auto)
TYPE_TEMPLATES: dict[str, str] = {
    Material.Type.SERVICE: "content/material_service.html",
    Material.Type.ARTICLE: "content/material_article.html",
    Material.Type.FAQ: "content/material_question.html",
    Material.Type.REQUIREMENT: "content/material_question.html",
    Material.Type.DOCUMENT: "content/material_document.html",
    Material.Type.INSTRUCTION: "content/material_document.html",
    Material.Type.ORDER_SAMPLE: "content/material_document.html",
    Material.Type.RISK_CARD: "content/material_document.html",
    Material.Type.PAGE: "content/material_page.html",
}

SPECIAL_TEMPLATES: dict[str, str] = {
    Material.Template.SERVICES_HUB: "pages/services_hub.html",
    Material.Template.PRICES: "pages/prices.html",
    Material.Template.CONTACTS: "pages/contacts.html",
    Material.Template.ABOUT: "pages/about.html",
    Material.Template.CLIENTS: "pages/clients.html",
    Material.Template.TERMS: "pages/terms.html",
    Material.Template.SITEMAP: "pages/sitemap.html",
}

# Подпись над заголовком по типу (если у материала не задана своя плашка)
TYPE_BADGES: dict[str, str] = {
    Material.Type.SERVICE: "Услуга",
    Material.Type.ARTICLE: "Статья",
    Material.Type.DOCUMENT: "Документ",
    Material.Type.INSTRUCTION: "Инструкция по охране труда",
    Material.Type.ORDER_SAMPLE: "Образец приказа",
    Material.Type.RISK_CARD: "Карта рисков",
    Material.Type.FAQ: "Вопрос",
    Material.Type.REQUIREMENT: "Требования охраны труда",
}

SORT_OPTIONS: dict[str, tuple[str, list[str]]] = {
    "popular": ("Популярные", ["-hits", "title"]),
    "new": ("Новые", ["-published_at"]),
    "alpha": ("По алфавиту", ["title"]),
}


def template_for(material: Material) -> str:
    """
    Выбирает шаблон страницы материала.

    Args:
        material: материал.

    Returns:
        Путь к шаблону Django.
    """
    if material.template != Material.Template.AUTO:
        return SPECIAL_TEMPLATES[material.template]
    return TYPE_TEMPLATES.get(material.type, "content/material_page.html")


def badge_for(material: Material) -> str:
    """Плашка над заголовком: своя или по типу."""
    return material.badge or TYPE_BADGES.get(material.type, "")


def schema_for(material: Material, url: str) -> dict[str, dict[str, object]]:
    """
    Разметка schema.org для материала: Service у услуг, FAQPage у вопросов.

    Args:
        material: материал.
        url: абсолютный адрес страницы.

    Returns:
        ``{"service_schema": …}`` / ``{"faq_schema": …}`` или пустой словарь.
    """
    if material.type == Material.Type.SERVICE:
        return {
            "service_schema": {
                "@context": "https://schema.org",
                "@type": "Service",
                "name": material.title,
                "url": url,
                "areaServed": "BY",
                "provider": {"@type": "ProfessionalService", "name": "СУОТ.BY"},
            }
        }
    if material.type == Material.Type.FAQ:
        answer = material.short_answer or material.search_text[:1000]
        return {
            "faq_schema": {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": material.title,
                        "acceptedAnswer": {"@type": "Answer", "text": answer},
                    }
                ],
            }
        }
    return {}


def register_hit(material: Material) -> None:
    """
    Увеличивает счётчик просмотров одним UPDATE без гонок (F-выражение).

    Args:
        material: просмотренный материал.
    """
    Material.objects.filter(pk=material.pk).update(hits=F("hits") + 1)


def search_materials(query: str, base: QuerySet[Material] | None = None) -> QuerySet[Material]:
    """
    Полнотекстовый поиск по материалам.

    На PostgreSQL — по tsvector с русской морфологией и ранжированием, на других БД — по вхождению.

    Args:
        query: строка поиска.
        base: исходная выборка (по умолчанию все опубликованные).

    Returns:
        Выборка найденных материалов, лучшие совпадения первыми.
    """
    qs = base if base is not None else Material.objects.published()
    query = query.strip()[:200]
    if not query:
        return qs.none()
    if connection.vendor == "postgresql":
        sq = SearchQuery(query, config="russian", search_type="websearch")
        return (
            qs.annotate(rank=SearchRank(F("search_vector"), sq))
            .filter(Q(search_vector=sq) | Q(title__icontains=query))
            .order_by("-rank", "-hits")
        )
    return qs.filter(Q(title__icontains=query) | Q(search_text__icontains=query)).order_by("-hits")


def category_materials(
    category: Category, sort: str = "popular", query: str = ""
) -> QuerySet[Material]:
    """
    Материалы раздела (включая подразделы первого уровня) с сортировкой и поиском.

    Args:
        category: раздел.
        sort: ключ из :data:`SORT_OPTIONS`.
        query: строка поиска внутри раздела.

    Returns:
        Выборка материалов.
    """
    ids = [category.pk, *category.children.values_list("pk", flat=True)]
    qs = Material.objects.published().filter(category_id__in=ids).select_related("category")
    if query:
        return search_materials(query, qs)
    return qs.order_by(*SORT_OPTIONS.get(sort, SORT_OPTIONS["popular"])[1])


def useful_tabs() -> QuerySet[Category]:
    """Вкладки раздела «Полезное» со счётчиками материалов."""
    return (
        Category.objects.filter(show_in_useful=True, is_published=True)
        .annotate(n=Count("materials", filter=Q(materials__is_published=True)))
        .order_by("ordering")
    )


def faq_sections() -> QuerySet[Category]:
    """Подразделы «Вопрос-ответ» со счётчиками, крупные первыми."""
    return (
        Category.objects.filter(kind=Category.Kind.FAQ, is_published=True, parent__isnull=False)
        .annotate(n=Count("materials", filter=Q(materials__is_published=True)))
        .order_by("-n", "title")
    )


def popular_questions(limit: int = 6) -> QuerySet[Material]:
    """Самые просматриваемые вопросы."""
    return Material.objects.published().filter(type=Material.Type.FAQ).order_by("-hits")[:limit]


@dataclass
class ServiceGroup:
    """Группа услуг для хаба «Все услуги»."""

    anchor: str
    title: str
    category: Category | None
    items: list[Material] = field(default_factory=list)


def service_groups() -> list[ServiceGroup]:
    """
    Услуги двумя группами: по охране труда и по СУОТ (по виду раздела).

    Returns:
        Список групп; услуги без раздела попадают в первую группу.
    """
    services = list(
        Material.objects.published()
        .filter(type=Material.Type.SERVICE)
        .select_related("category")
        .order_by("ordering", "title")
    )
    cats = {
        c.kind: c
        for c in Category.objects.filter(
            kind__in=[Category.Kind.SERVICES_OT, Category.Kind.SERVICES_SUOT]
        )
    }
    ot = ServiceGroup("ot", "Услуги по охране труда", cats.get(Category.Kind.SERVICES_OT))
    suot = ServiceGroup("suot", "Разработка СУОТ", cats.get(Category.Kind.SERVICES_SUOT))
    for s in services:
        (
            suot if s.category and s.category.kind == Category.Kind.SERVICES_SUOT else ot
        ).items.append(s)
    return [ot, suot]


def related_for(material: Material, limit: int = 4) -> list[Material]:
    """
    Связанные материалы: сначала указанные вручную, потом популярные из того же раздела.

    Args:
        material: текущий материал.
        limit: сколько вернуть.

    Returns:
        Список материалов без текущего.
    """
    manual = list(material.related.filter(is_published=True)[:limit])
    if len(manual) >= limit or not material.category_id:
        return manual
    extra = (
        Material.objects.published()
        .filter(category_id=material.category_id)
        .exclude(pk__in=[material.pk, *[m.pk for m in manual]])
        .order_by("-hits")[: limit - len(manual)]
    )
    return manual + list(extra)


def sitemap_tree() -> list[dict[str, object]]:
    """
    Дерево для HTML-карты сайта: служебные страницы, услуги, разделы с материалами.

    Returns:
        Список групп ``{"title", "url", "items": [(title, url)], "count"}``.
    """
    groups: list[dict[str, object]] = []
    for g in service_groups():
        groups.append(
            {
                "title": g.title,
                "url": "/uslugi-po-ohrane-truda-v-minske-i-po-belarusi.html",
                "items": [(m.title, m.path) for m in g.items],
                "count": len(g.items),
            }
        )
    roots = Category.objects.filter(
        is_published=True, path__isnull=False, parent__isnull=True
    ).order_by("ordering")
    for cat in roots:
        mats = list(category_materials(cat, "alpha"))
        groups.append(
            {
                "title": cat.title,
                "url": cat.path,
                "items": [(m.title, m.path) for m in mats],
                "count": len(mats),
            }
        )
    pages = Material.objects.published().filter(type=Material.Type.PAGE).order_by("title")
    groups.append(
        {
            "title": "О компании",
            "url": "/o-nas.html",
            "items": [(m.title, m.path) for m in pages],
            "count": pages.count(),
        }
    )
    return groups
