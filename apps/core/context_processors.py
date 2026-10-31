# apps/core/context_processors.py — данные шапки и подвала во всех шаблонах
from __future__ import annotations

from typing import Any

from django.conf import settings
from django.http import HttpRequest

from apps.core.models import SiteSettings

# ✏️ ИЗМЕНЕНО: две группы старого меню Joomla раскрываются отдельно; адреса сохранены.
MAIN_MENU: list[dict[str, Any]] = [
    {
        "key": "uslugi",
        "label": "Услуги по охране труда",
        "url": "/uslugi-po-ohrane-truda-v-minske-i-po-belarusi.html",
        "children": [
            {
                "label": "Разработка документов по ОТ",
                "url": "/razrabotka-vsej-neobhodimoj-dlya-predpriyatiya-dokumentacii-po-ohrane-truda.html",
            },
            {
                "label": "Организация охраны труда",
                "url": "/organizaciya-raboty-po-ohrane-truda-v-organizacii.html",
                "aliases": [
                    "/kachestvennaya-razrabotka-dokumentov-po-ohrane-truda-individualno-dlya-vashej-organizacii.html"
                ],
            },
            {"label": "Аудит по охране труда", "url": "/audit-ohrany-truda-na-predpriyatii.html"},
            {"label": "Консультации по ОТ", "url": "/konsultacii-po-voprosam-ohrany-truda.html"},
            {
                "label": "Обслуживание организаций",
                "url": "/obsluzhivanie-organizacii-v-kachestve-specialista-po-ohrane-truda.html",
            },
            {
                "label": "Выполнение предписаний по ОТ",
                "url": "/vypolnenie-predpisanij-po-ohrane-truda.html",
            },
            {
                "label": "Проведение семинаров",
                "url": "/seminary-po-ohrane-truda-pozharnoj-bezopasnosti.html",
            },
            {
                "label": "Все услуги по охране труда",
                "url": "/uslugi-po-ohrane-truda-v-minske-i-po-belarusi.html",
            },
        ],
    },
    {
        "key": "suot",
        "label": "Разработка СУОТ",
        "url": "/razrabotka-i-vnedrenie-suot-pod-klyuch.html",
        "children": [
            {
                "label": "Идентификация рисков",
                "url": "/razrabotka-kart-opasnostej-i-riskov-dlya-vashej-organizacii.html",
            },
            {
                "label": "Разработка инструкций по ОТ",
                "url": "/razrabotka-instrukcij-po-ohrane-truda-v-minske-i-belarusi.html",
            },
            {
                "label": "ОТ в должностных инструкциях",
                "url": "/funkcionalnye-obyazannosti-po-ohrane-truda-v-dolzhnostnyh-instrukciyah.html",
            },
            {
                "label": "Разработка приказов по ОТ",
                "url": "/razrabotka-prikazov-rasporyazhenij-po-ohrane-truda.html",
            },
            {
                "label": "Журналы по охране труда",
                "url": "/zhurnaly-po-ohrane-truda-i-po-otdelnym-proceduram-suot.html",
            },
            {
                "label": "Сертификация СУОТ",
                "url": "/sertifikaciya-sistemy-upravleniya-ohranoj-truda-suot.html",
            },
            {
                "label": "Актуализация СУОТ",
                "url": "/podderzhanie-suot-v-rabotosposobnom-sostoyanii.html",
            },
            {"label": "Все услуги по СУОТ", "url": "/pages/more-pages/vse-uslugi-po-suot.html"},
        ],
    },
    {"key": "ceny", "label": "Цены", "url": "/ceny-na-razrabotku-suot-v-minske.html"},
    {"key": "poleznoe", "label": "Полезное", "url": "/prikazy-po-ohrane-truda/"},
    {"key": "faq", "label": "Вопрос-ответ", "url": "/chasto-zadavaemye-voprosy-po-ohrane-truda/"},
    {"key": "o-nas", "label": "О нас", "url": "/o-nas.html"},
    {"key": "kontakty", "label": "Контакты", "url": "/kontakty.html"},
]


def site(request: HttpRequest) -> dict[str, Any]:
    """
    Добавляет в контекст настройки сайта, меню и канонический адрес текущей страницы.

    Args:
        request: текущий запрос.

    Returns:
        Словарь с ключами ``site``, ``main_menu``, ``canonical_url``, ``site_url``, ``metrika_id``.
    """
    site_settings = SiteSettings.load()
    # schema.org Organization — в каждой странице (контакты для поисковиков)
    org_schema: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "name": site_settings.brand,
        "description": site_settings.tagline,
        "url": settings.SITE_URL,
        "telephone": site_settings.phones,
        "areaServed": "BY",
        "address": {"@type": "PostalAddress", "addressLocality": "Минск", "addressCountry": "BY"},
    }
    if site_settings.email:
        org_schema["email"] = site_settings.email
    # 💡 canonical — всегда без GET-параметров (utm, gclid и т. п. — правило из redirects.csv)
    return {
        "site": site_settings,
        "org_schema": org_schema,
        # 💡 Отдельные словари на запрос: подсветка не меняет глобальное меню.
        "main_menu": [
            {
                **item,
                "is_current": request.path == item["url"],
                "is_active": request.path == item["url"]
                or any(
                    request.path in [child["url"], *child.get("aliases", [])]
                    for child in item.get("children", [])
                ),
                "children": [
                    {
                        **child,
                        "is_current": request.path in [child["url"], *child.get("aliases", [])],
                    }
                    for child in item.get("children", [])
                ],
            }
            for item in MAIN_MENU
        ],
        "site_url": settings.SITE_URL,
        "canonical_url": settings.SITE_URL + request.path,
        "metrika_id": settings.YANDEX_METRIKA_ID,
    }
