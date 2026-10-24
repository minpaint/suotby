# apps/seo/sitemaps.py — sitemap.xml
from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from django.contrib.sitemaps import Sitemap
from django.db.models import QuerySet

from apps.content.models import Category, Material


class StaticSitemap(Sitemap):
    """Главная."""

    priority = 1.0
    changefreq = "weekly"
    protocol = "https"

    def items(self) -> list[str]:
        return ["/"]

    def location(self, item: str) -> str:
        return item


class MaterialSitemap(Sitemap):
    """Все опубликованные материалы. Приоритет — по типу: услуги выше справочных страниц."""

    protocol = "https"
    changefreq = "monthly"
    PRIORITY: ClassVar[dict[str, float]] = {"service": 0.9, "page": 0.7, "article": 0.6}

    def items(self) -> QuerySet[Material]:
        return Material.objects.published().order_by("pk")

    def location(self, item: Material) -> str:
        return item.path

    def lastmod(self, item: Material) -> datetime:
        return item.updated_at

    def priority(self, item: Material) -> float:
        return self.PRIORITY.get(item.type, 0.5)


class CategorySitemap(Sitemap):
    """Разделы со своей страницей (в т. ч. 13 подразделов «Вопрос-ответ», которых не было в старой карте)."""

    protocol = "https"
    changefreq = "weekly"
    priority = 0.6

    def items(self) -> QuerySet[Category]:
        return Category.objects.filter(is_published=True, path__isnull=False).order_by("pk")

    def location(self, item: Category) -> str:
        return item.path or "/"


SITEMAPS = {"static": StaticSitemap, "categories": CategorySitemap, "materials": MaterialSitemap}
