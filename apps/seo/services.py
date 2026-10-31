# apps/seo/services.py — правила переадресации старого сайта
"""
Правила адресов со старого suot.by (см. docs/data/redirects.csv).

Точные пары «старый → новый» лежат в таблицах :class:`Redirect` и :class:`Gone` и кэшируются целиком
(их несколько сотен). Правила с ``*`` из таблицы реализованы здесь кодом:

* ``www.suot.by`` и прочие зеркала → ``suot.by`` (одним шагом);
* ``/index.php`` → ``/``;
* ``/en/<путь>`` → ``/<путь>``;
* ``/<раздел>/page-N.html`` → ``/<раздел>/`` (старая пагинация Joomla);
* битые варианты тире в ``razrabotka-sistemy-…-eto-obyazatelno.html`` → чистый адрес.
"""

from __future__ import annotations

import re

from django.core.cache import cache

from apps.seo.models import Gone, Redirect

MAPS_CACHE_KEY = "seo:maps:v1"
CLEAN_OBYAZATELNO = "/razrabotka-sistemy-upravleniya-ohranoj-truda-eto-obyazatelno.html"

_PAGINATION_RE = re.compile(r"^(?P<dir>/(?:[^/]+/)+)page-\d+\.html$", re.IGNORECASE)
_OBYAZATELNO_RE = re.compile(
    r"^/razrabotka-sistemy-upravleniya-ohranoj-truda-.+-eto-obyazatelno\.html$"
)


def load_maps() -> tuple[dict[str, tuple[str, int]], set[str]]:
    """
    Таблицы переадресаций и 410 из кэша (или базы).

    Returns:
        ``({old_path: (new_path, code)}, {gone_path, …})``.
    """
    maps = cache.get(MAPS_CACHE_KEY)
    if maps is None:
        redirects = {r.old_path: (r.new_path, r.code) for r in Redirect.objects.all()}
        gone = set(Gone.objects.values_list("path", flat=True))
        maps = (redirects, gone)
        cache.set(MAPS_CACHE_KEY, maps, 3600)
    return maps


def reset_maps() -> None:
    """Сбрасывает кэш таблиц (после правки в админке или импорта)."""
    cache.delete(MAPS_CACHE_KEY)


def pattern_redirect(path: str) -> str | None:
    """
    Правила с ``*`` из redirects.csv.

    Args:
        path: путь запроса (уже раскодированный).

    Returns:
        Новый путь или None, если правило не подходит.
    """
    if path == "/index.php":
        return "/"
    if path.startswith("/en/"):
        return path[3:]
    if path == "/en":
        return "/"
    m = _PAGINATION_RE.match(path)
    if m:
        return m.group("dir")
    if path != CLEAN_OBYAZATELNO and _OBYAZATELNO_RE.match(path):
        return CLEAN_OBYAZATELNO
    return None


def resolve(path: str) -> tuple[str, int] | None:
    """
    Решает, что делать со старым адресом.

    Args:
        path: путь запроса.

    Returns:
        ``(new_path, code)`` для переадресации, ``("", 410)`` для удалённого адреса, None — обработать как обычно.
    """
    redirects, gone = load_maps()
    if path in redirects:
        new_path, code = redirects[path]
        return (new_path, code) if new_path != path else None
    if path in gone:
        return ("", 410)
    pattern_path = pattern_redirect(path)
    if pattern_path and pattern_path != path:
        # 💡 цепочки сводим в один шаг: /en/about → /about → /o-nas.html
        if pattern_path in redirects:
            return (redirects[pattern_path][0], 301)
        return (pattern_path, 301)
    return None
