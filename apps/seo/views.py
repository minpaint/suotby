# apps/seo/views.py — robots.txt
from __future__ import annotations

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET


@require_GET
@cache_page(3600)
def robots_txt(request: HttpRequest) -> HttpResponse:
    """
    robots.txt.

    🔐 Адрес админки сюда намеренно не пишется: robots.txt читают и боты-сканеры.
    """
    lines = [
        "User-agent: *",
        "Disallow: /poisk/",
        "Disallow: /zayavka/",
        "Disallow: /*?utm_",
        "Disallow: /*?q=",
        "",
        f"Sitemap: {settings.SITE_URL}/sitemap.xml",
        f"Host: {settings.SITE_URL}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")
