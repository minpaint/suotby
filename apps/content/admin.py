# apps/content/admin.py — админка разделов, материалов, цен
from __future__ import annotations

from typing import Any

from django import forms
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html
from django_ckeditor_5.widgets import CKEditor5Widget

from apps.content.models import Category, Material, PriceItem, ServiceFAQ


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"
        widgets = {"description": CKEditor5Widget(config_name="default")}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    list_display = ("title", "path", "kind", "parent", "show_in_useful", "ordering", "is_published")
    list_filter = ("kind", "is_published", "show_in_useful")
    list_editable = ("ordering", "is_published")
    search_fields = ("title", "path")


class MaterialForm(forms.ModelForm):
    """Форма материала с CKEditor 5 для текстовых полей (HTML всё равно чистится в save)."""

    class Meta:
        model = Material
        fields = "__all__"
        widgets = {
            "intro": CKEditor5Widget(config_name="default"),
            "body": CKEditor5Widget(config_name="default"),
            "basis": CKEditor5Widget(config_name="default"),
            "short_answer": forms.Textarea(attrs={"rows": 3}),
        }


class ServiceFAQInline(admin.StackedInline):
    model = ServiceFAQ
    extra = 0


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    form = MaterialForm
    list_display = (
        "title",
        "type",
        "category",
        "open_link",
        "hits",
        "npa_checked_at",
        "is_published",
    )
    list_filter = (
        "type",
        "is_published",
        "is_featured",
        "category",
        ("npa_checked_at", admin.EmptyFieldListFilter),
    )
    search_fields = ("title", "path", "legacy_id")
    list_select_related = ("category",)
    autocomplete_fields = ("related",)
    readonly_fields = ("legacy_id", "legacy_url", "hits", "rating_avg", "rating_votes")
    inlines = (ServiceFAQInline,)
    actions = ("mark_npa_checked", "publish", "unpublish")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "type",
                    "template",
                    "category",
                    "badge",
                    "is_published",
                    "is_featured",
                    "ordering",
                )
            },
        ),
        (
            "Адрес",
            {
                "fields": ("slug", "path"),
                "description": "⚠️ У страниц со старого сайта адрес менять нельзя — потеряются позиции в поиске.",
            },
        ),
        ("Текст", {"fields": ("short_answer", "intro", "body", "basis")}),
        ("Услуга", {"fields": ("price_from", "price_unit"), "classes": ("collapse",)}),
        ("Файлы", {"fields": ("file", "file_pdf", "cover")}),
        ("Проверка НПА", {"fields": ("audit_flags", "npa_checked_at")}),
        ("Связи", {"fields": ("related",)}),
        (
            "SEO",
            {
                "fields": ("meta_title", "meta_description", "meta_keywords"),
                "classes": ("collapse",),
            },
        ),
        ("Даты", {"fields": ("published_at", "updated_at")}),
        (
            "Старый сайт",
            {
                "fields": ("legacy_id", "legacy_url", "hits", "rating_avg", "rating_votes"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="На сайте")
    def open_link(self, obj: Material) -> str:
        return format_html('<a href="{}" target="_blank" rel="noopener">{}</a>', obj.path, obj.path)

    @admin.action(description="Отметить: ссылки на НПА проверены сегодня")
    def mark_npa_checked(self, request: HttpRequest, queryset: QuerySet[Material]) -> None:
        from django.utils import timezone

        n = queryset.update(npa_checked_at=timezone.localdate())
        self.message_user(request, f"Отмечено материалов: {n}")

    @admin.action(description="Опубликовать")
    def publish(self, request: HttpRequest, queryset: QuerySet[Material]) -> None:
        queryset.update(is_published=True)

    @admin.action(description="Снять с публикации")
    def unpublish(self, request: HttpRequest, queryset: QuerySet[Material]) -> None:
        queryset.update(is_published=False)

    def save_model(self, request: HttpRequest, obj: Material, form: Any, change: bool) -> None:
        from django.utils import timezone

        obj.updated_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(PriceItem)
class PriceItemAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "price", "unit", "show_on_home", "ordering", "is_published")
    list_filter = ("kind", "is_published")
    list_editable = ("price", "ordering", "is_published", "show_on_home")
