# apps/seo/middleware.py — переадресации старого сайта и 410
from __future__ import annotations

from collections.abc import Callable
from urllib.parse import quote

from django.conf import settings
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseGone,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.template.loader import render_to_string

from apps.seo.services import resolve


class LegacyRedirectMiddleware:
    """
    Обрабатывает запрос до роутера:

    1. зеркала (``www.suot.by``) → канонический хост одним 301;
    2. точные переадресации и 410 из таблиц;
    3. правила с ``*`` (``/en/…``, пагинация, битое тире).

    ⚠️ Админка и статика не трогаются, чтобы правило не могло сломать вход.
    """

    SKIP_PREFIXES = ("/static/", "/media/", "/ckeditor5/")

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.admin_prefix = "/" + settings.ADMIN_URL

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.process(request)
        return response if response is not None else self.get_response(request)

    def process(self, request: HttpRequest) -> HttpResponse | None:
        """
        Args:
            request: запрос.

        Returns:
            Ответ-переадресацию / 410 или None, если запрос нужно обработать как обычно.
        """
        host = request.get_host().split(":")[0].lower()
        canonical = settings.CANONICAL_HOST
        if host.startswith("www.") and host[4:] == canonical:
            return HttpResponsePermanentRedirect(f"https://{canonical}{request.get_full_path()}")

        path = request.path
        if path.startswith(self.SKIP_PREFIXES) or path.startswith(self.admin_prefix):
            return None
        result = resolve(path)
        if result is None:
            return None
        new_path, code = result
        if code == 410:
            return HttpResponseGone(render_to_string("410.html", request=request))
        # Параметры запроса (utm и т. п.) переносим как есть
        qs = request.META.get("QUERY_STRING", "")
        target = quote(new_path, safe="/:?=&%#()") + (
            f"?{qs}" if qs and "?" not in new_path else ""
        )
        if code == 302:
            return HttpResponseRedirect(target)
        return HttpResponsePermanentRedirect(target)
