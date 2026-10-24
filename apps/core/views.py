# apps/core/views.py — главная и страницы ошибок
from __future__ import annotations

from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseServerError
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import TemplateView

from apps.content import services
from apps.content.models import Material, PriceItem


class HomeView(TemplateView):
    """
    Главная по макету Main: блоки статичны, услуги, цены и вопросы — из базы.

    ⚠️ Целиком страницу не кэшируем: в ней форма с CSRF-токеном. Кэшируются блоки списков
    в шаблоне (``{% cache %}``) на ``PAGE_CACHE_SECONDS``.
    """

    template_name = "pages/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        featured = Material.objects.published().filter(type=Material.Type.SERVICE, is_featured=True)
        if not featured.exists():
            # 💡 пока в админке не отмечены услуги «на главной» — показываем самые посещаемые
            featured = (
                Material.objects.published().filter(type=Material.Type.SERVICE).order_by("-hits")
            )
        ctx["services"] = featured.order_by("ordering", "-hits")[:6]
        ctx["tariffs"] = PriceItem.objects.filter(
            is_published=True, kind=PriceItem.Kind.TARIFF, show_on_home=True
        )[:3]
        ctx["questions"] = services.popular_questions(4)
        ctx["useful"] = services.useful_tabs()
        ctx["cache_seconds"] = settings.PAGE_CACHE_SECONDS
        return ctx


def page_not_found(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    """Настоящая 404 (с кодом 404, а не «мягкая» страница с кодом 200, как было в Joomla)."""
    return render(request, "404.html", {"popular": services.popular_questions(3)}, status=404)


def server_error(request: HttpRequest) -> HttpResponse:
    """500 без обращения к базе (она может быть причиной ошибки)."""
    return HttpResponseServerError(render_to_string("500.html"))
