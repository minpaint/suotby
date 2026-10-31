# apps/core/templatetags/site_tags.py — мелкие помощники шаблонов
from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from django import template
from django.utils.html import format_html
from django.utils.safestring import SafeString

from apps.core import icons
from apps.core.models import SiteSettings
from apps.core.sanitize import mark_clean

register = template.Library()


@register.filter
def tel(phone: str) -> str:
    """«+375 29 357-09-11» → «tel:+375293570911»."""
    return SiteSettings.tel_href(phone or "")


@register.simple_tag
def price_label(value: Decimal | str | None, unit: str = "") -> str:
    """
    Подпись цены: «от 300 BYN/мес» или «по запросу», если цена не задана.

    Args:
        value: число или готовая строка.
        unit: единица («/мес»).
    """
    if value in (None, ""):
        return "по запросу"
    if isinstance(value, Decimal):
        value = f"{value.normalize():f}".rstrip(".")
        return f"от {value} BYN{unit}"
    text = str(value)
    return text if "BYN" in text or not any(ch.isdigit() for ch in text) else f"{text} BYN{unit}"


@register.simple_tag
def json_ld(data: dict[str, Any]) -> SafeString:
    """
    Безопасно выводит JSON-LD (schema.org).

    🔐 Экранирует «<», чтобы текст материала не мог закрыть тег <script>.
    """
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    return mark_clean(f'<script type="application/ld+json">{payload}</script>')


@register.simple_tag
def icon(name: str, size: int = 24) -> SafeString:
    """Линейная иконка из набора ``apps.core.icons``: ``{% icon "phone" 18 %}`` или ``{% icon s.title|icon_for %}``."""
    # 💡 разметка собирается только из констант набора — пользовательский текст в неё не попадает
    return mark_clean(icons.svg(name, size))


@register.filter
def icon_for(text: str) -> str:
    """Имя иконки по названию услуги или раздела."""
    return icons.icon_for(text)


@register.filter
def type_icon(material_type: str) -> str:
    """Имя иконки по типу материала (инструкция, приказ, вопрос…)."""
    return icons.TYPE_ICONS.get(material_type, icons.DEFAULT_ICON)


@register.simple_tag
def check_icon(color: str = "#9FD0AE", size: int = 22) -> SafeString:
    """Иконка «галочка» из макетов (декоративная)."""
    return format_html(
        '<svg width="{0}" height="{0}" viewBox="0 0 22 22" aria-hidden="true"><path d="M4 11.5l4.5 4.5L18 6" '
        'fill="none" stroke="{1}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        size,
        color,
    )
