# tests/factories.py — фабрики тестовых данных (factory-boy)
from __future__ import annotations

import factory

from apps.content.models import Category, Material


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    title = factory.Sequence(lambda n: f"Раздел {n}")
    slug = factory.Sequence(lambda n: f"razdel-{n}")
    path = factory.LazyAttribute(lambda o: f"/{o.slug}/")
    kind = Category.Kind.ARTICLES


class MaterialFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Material

    title = factory.Sequence(lambda n: f"Материал {n}")
    slug = factory.Sequence(lambda n: f"material-{n}")
    type = Material.Type.ARTICLE
    body = "<p>Текст материала об охране труда.</p>"
