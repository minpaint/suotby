# apps/core/sanitize.py — очистка HTML из админки и импорта
"""
🔐 Санитайзер HTML на nh3 (Rust-реализация ammonia).

Любой HTML, который попадает в базу (редактор CKEditor, импорт из Joomla), проходит через
:func:`clean_html`. Разрешён только белый список тегов и атрибутов: скрипты, стили, обработчики
событий, iframe и `javascript:`-ссылки вырезаются. Это защищает от хранимого XSS, даже если
учётную запись редактора скомпрометируют.
"""

from __future__ import annotations

import re

import nh3
from django.utils.safestring import SafeString, mark_safe

# Теги, которые реально нужны текстам о охране труда: заголовки, списки, таблицы, картинки, цитаты
ALLOWED_TAGS: set[str] = {
    "p",
    "br",
    "hr",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "s",
    "sup",
    "sub",
    "mark",
    "small",
    "ul",
    "ol",
    "li",
    "blockquote",
    "pre",
    "code",
    "a",
    "img",
    "figure",
    "figcaption",
    "table",
    "thead",
    "tbody",
    "tfoot",
    "tr",
    "th",
    "td",
    "caption",
    "colgroup",
    "col",
    "div",
    "span",
}

ALLOWED_ATTRIBUTES: dict[str, set[str]] = {
    "a": {"href", "title", "target"},
    "img": {"src", "alt", "title", "width", "height", "loading"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan", "scope"},
    "col": {"span"},
    "ol": {"start", "type"},
    # id нужен для якорей оглавления в статьях
    "h2": {"id"},
    "h3": {"id"},
}

ALLOWED_URL_SCHEMES: set[str] = {"http", "https", "mailto", "tel"}

# h1 на странице один — заголовок материала, поэтому h1 из текста понижаем до h2
_H1_RE = re.compile(r"<(/?)h1(\s[^>]*)?>", re.IGNORECASE)
# Пустые абзацы, которые оставляют редакторы и конструктор страниц
_EMPTY_P_RE = re.compile(r"<p>(\s|&nbsp;|<br\s*/?>)*</p>", re.IGNORECASE)


def clean_html(html: str | None) -> str:
    """
    Очищает HTML по белому списку.

    Args:
        html: исходный HTML (может быть None или пустым).

    Returns:
        Безопасный HTML без скриптов, стилей, iframe и опасных атрибутов.
    """
    if not html:
        return ""
    html = _H1_RE.sub(lambda m: f"<{m.group(1)}h2>", html)
    cleaned = nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
        # ⚠️ содержимое этих тегов удаляется целиком, а не только сами теги
        clean_content_tags={"script", "style", "iframe", "object", "embed", "noscript", "template"},
        link_rel="noopener noreferrer",
        strip_comments=True,
    )
    cleaned = _EMPTY_P_RE.sub("", cleaned)
    return cleaned.strip()


def clean_text(value: str | None) -> str:
    """
    Убирает из строки любые теги — для полей, где HTML не нужен (короткий ответ, подписи).

    Args:
        value: исходная строка.

    Returns:
        Текст без тегов, с нормализованными пробелами.
    """
    if not value:
        return ""
    text = nh3.clean(value, tags=set(), attributes={}, clean_content_tags={"script", "style"})
    return re.sub(r"\s+", " ", text).strip()


def mark_clean(html: str) -> SafeString:
    """
    Помечает HTML как безопасный для шаблона.

    ✅ Вызывать только для HTML, прошедшего :func:`clean_html` (или собранного из экранированных данных).
    Единственное место в проекте с ``mark_safe`` — проще проверять при ревью.
    """
    return mark_safe(html)  # noqa: S308  # nosec B308 B703
