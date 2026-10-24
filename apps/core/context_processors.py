# apps/core/context_processors.py — данные шапки и подвала во всех шаблонах
from __future__ import annotations

from typing import Any

from django.conf import settings
from django.http import HttpRequest

from apps.core.models import SiteSettings

# Главное меню (из макета Shapka): ключ — для подсветки активного пункта, путь — старый адрес сайта
MAIN_MENU: list[dict[str, str]] = [
    {
        "key": "uslugi",
        "label": "Услуги",
        "url": "/uslugi-po-ohrane-truda-v-minske-i-po-belarusi.html",
    },
    {
        "key": "suot",
        "label": "Разработка СУОТ",
        "url": "/razrabotka-i-vnedrenie-suot-pod-klyuch.html",
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
        "main_menu": MAIN_MENU,
        "site_url": settings.SITE_URL,
        "canonical_url": settings.SITE_URL + request.path,
        "metrika_id": settings.YANDEX_METRIKA_ID,
    }
