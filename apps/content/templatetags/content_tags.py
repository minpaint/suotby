# apps/content/templatetags/content_tags.py — оглавление статей и подписи материалов
from __future__ import annotations

import re
from typing import Any

from django import template
from django.utils.html import strip_tags
from django.utils.safestring import SafeString
from django.utils.text import slugify

from apps.core.sanitize import mark_clean

register = template.Library()

_H2_RE = re.compile(r"<h2(?P<attrs>[^>]*)>(?P<text>.*?)</h2>", re.IGNORECASE | re.DOTALL)
_TRANSLIT = str.maketrans(
    {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "j",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "c",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
    }
)


def _anchor(text: str, used: set[str]) -> str:
    """Латинский якорь из заголовка, уникальный в пределах страницы."""
    base = slugify(strip_tags(text).lower().translate(_TRANSLIT))[:60] or "razdel"
    anchor, n = base, 2
    while anchor in used:
        anchor, n = f"{base}-{n}", n + 1
    used.add(anchor)
    return anchor


@register.filter
def with_toc(html: str) -> dict[str, Any]:
    """
    Проставляет id заголовкам h2 и собирает оглавление.

    Args:
        html: очищенный HTML материала.

    Returns:
        ``{"html": SafeString, "toc": [(id, текст)]}``.
    """
    used: set[str] = set()
    toc: list[tuple[str, str]] = []

    def repl(m: re.Match[str]) -> str:
        text = m.group("text")
        anchor = _anchor(text, used)
        toc.append((anchor, strip_tags(text).strip()))
        return f'<h2 id="{anchor}">{text}</h2>'

    # ✅ html уже прошёл nh3 при сохранении, поэтому mark_safe здесь допустим
    result = _H2_RE.sub(repl, html or "")
    return {"html": mark_clean(result), "toc": toc}


@register.filter
def safe_html(html: str) -> SafeString:
    """Вывод HTML материала. ✅ Текст очищен санитайзером при сохранении (Material.save)."""
    return mark_clean(html or "")
