# apps/content/views.py — страницы материалов, разделов, поиска
"""
Представления контента.

⚠️ :class:`PageResolverView` — «последний» маршрут: всё, что не перехватили другие адреса,
ищется сначала среди материалов, затем среди разделов по полному ``path``. Так новый сайт
отвечает ровно по старым адресам Joomla.
"""

from __future__ import annotations

from typing import Any

from django.core.paginator import Paginator
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView

from apps.content import services
from apps.content.models import Category, Material, PriceItem
from apps.core.models import Client, TeamMember, Testimonial

PER_PAGE = 20


class PageResolverView(View):
    """Находит материал или раздел по полному адресу и отдаёт нужный шаблон."""

    def get(self, request: HttpRequest, path: str = "") -> HttpResponse:
        """
        Args:
            request: запрос.
            path: путь без ведущего слеша (из маршрута).

        Returns:
            Страницу материала или раздела.

        Raises:
            Http404: если по адресу ничего не опубликовано.
        """
        full_path = "/" + path
        material = (
            Material.objects.published()
            .select_related("category", "category__parent")
            .filter(path=full_path)
            .first()
        )
        if material is not None:
            return self.render_material(request, material)
        category = (
            Category.objects.filter(path=full_path, is_published=True)
            .select_related("parent")
            .first()
        )
        if category is not None:
            return self.render_category(request, category)
        raise Http404("Страница не найдена")

    # ------------------------------------------------------------------ материал
    def render_material(self, request: HttpRequest, material: Material) -> HttpResponse:
        """Собирает контекст материала и рендерит шаблон по типу или спецшаблон."""
        services.register_hit(material)
        ctx: dict[str, Any] = {
            "material": material,
            "badge": services.badge_for(material),
            "breadcrumbs": self.material_breadcrumbs(material),
            "related": services.related_for(material),
            "menu_active": self.menu_key(material),
        }
        tpl = services.template_for(material)
        ctx.update(services.schema_for(material, request.build_absolute_uri(material.path)))
        if material.type == Material.Type.SERVICE:
            ctx["service_faqs"] = material.service_faqs.all()
            ctx["other_services"] = (
                Material.objects.published()
                .filter(type=Material.Type.SERVICE)
                .exclude(pk=material.pk)
                .order_by("-hits")[:3]
            )
            ctx["service_questions"] = material.related.filter(
                is_published=True, type__in=[Material.Type.FAQ, Material.Type.ARTICLE]
            )[:4]
        if material.template == Material.Template.SERVICES_HUB:
            ctx["groups"] = services.service_groups()
        elif material.template == Material.Template.PRICES:
            items = PriceItem.objects.filter(is_published=True)
            ctx["tariffs"] = items.filter(kind=PriceItem.Kind.TARIFF)
            ctx["rows"] = items.filter(kind=PriceItem.Kind.ROW)
        elif material.template == Material.Template.ABOUT:
            ctx["team"] = TeamMember.objects.filter(is_published=True)
            featured = list(Client.objects.filter(is_featured=True))
            ctx["featured_clients"] = featured
            ctx["clients_more"] = Client.objects.count() - len(featured)
        elif material.template == Material.Template.CLIENTS:
            ctx["clients"] = Client.objects.all()
            ctx["testimonials"] = Testimonial.objects.filter(is_published=True)
        elif material.template == Material.Template.SITEMAP:
            ctx["tree"] = services.sitemap_tree()
        return render(request, tpl, ctx)

    @staticmethod
    def material_breadcrumbs(material: Material) -> list[tuple[str, str | None]]:
        """Хлебные крошки: главная → раздел (если у него есть страница) → материал."""
        crumbs: list[tuple[str, str | None]] = [("Главная", "/")]
        cat = material.category
        if material.type == Material.Type.SERVICE:
            crumbs.append(("Услуги", "/uslugi-po-ohrane-truda-v-minske-i-po-belarusi.html"))
        elif cat is not None:
            if cat.parent is not None and cat.parent.path:
                crumbs.append((cat.parent.short_title, cat.parent.path))
            if cat.path:
                crumbs.append((cat.short_title, cat.path))
        crumbs.append((material.title, None))
        return crumbs

    @staticmethod
    def menu_key(material: Material) -> str:
        """Ключ активного пункта главного меню."""
        if (
            material.type == Material.Type.SERVICE
            or material.template == Material.Template.SERVICES_HUB
        ):
            return "uslugi"
        if material.type in Material.QUESTION_TYPES:
            return "faq"
        by_template: dict[str, str] = {
            Material.Template.PRICES: "ceny",
            Material.Template.CONTACTS: "kontakty",
            Material.Template.ABOUT: "o-nas",
            Material.Template.CLIENTS: "o-nas",
        }
        if material.template in by_template:
            return by_template[material.template]
        return "" if material.type == Material.Type.PAGE else "poleznoe"

    # ------------------------------------------------------------------ раздел
    def render_category(self, request: HttpRequest, category: Category) -> HttpResponse:
        """Список материалов раздела с поиском, сортировкой и пагинацией, либо хаб «Вопрос-ответ»."""
        if category.template == Category.Template.FAQ_HUB:
            return render(
                request,
                "content/faq_hub.html",
                {
                    "category": category,
                    "sections": services.faq_sections(),
                    "top": services.popular_questions(6),
                    "total": Material.objects.published().filter(type=Material.Type.FAQ).count(),
                    "menu_active": "faq",
                },
            )
        sort = request.GET.get("sort", "popular")
        if sort not in services.SORT_OPTIONS:
            sort = "popular"
        query = request.GET.get("q", "").strip()
        page = Paginator(services.category_materials(category, sort, query), PER_PAGE).get_page(
            request.GET.get("page")
        )
        crumbs: list[tuple[str, str | None]] = [("Главная", "/")]
        if category.parent is not None and category.parent.path:
            crumbs.append((category.parent.short_title, category.parent.path))
        crumbs.append((category.title, None))
        is_faq = category.kind == Category.Kind.FAQ
        return render(
            request,
            "content/category.html",
            {
                "category": category,
                "page_obj": page,
                "sort": sort,
                "sort_options": [(k, v[0]) for k, v in services.SORT_OPTIONS.items()],
                "query": query,
                "tabs": services.useful_tabs(),
                "breadcrumbs": crumbs,
                "popular": services.popular_questions(3),
                "menu_active": "faq" if is_faq else "poleznoe",
            },
        )


class SearchView(TemplateView):
    """Поиск по сайту: /poisk/?q=…"""

    template_name = "content/search.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()
        ctx["query"] = query
        ctx["page_obj"] = Paginator(services.search_materials(query), PER_PAGE).get_page(
            self.request.GET.get("page")
        )
        return ctx
