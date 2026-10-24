# apps/core/admin.py — админка настроек сайта, клиентов, отзывов, команды
from __future__ import annotations

from typing import Any

from django import forms
from django.contrib import admin
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from django_ckeditor_5.widgets import CKEditor5Widget

from apps.core.models import Client, SiteSettings, TeamMember, Testimonial

admin.site.site_header = "СУОТ.BY — управление сайтом"
admin.site.site_title = "СУОТ.BY"
admin.site.index_title = "Разделы"


class SiteSettingsForm(forms.ModelForm):
    """Форма настроек с визуальным редактором для политик."""

    class Meta:
        model = SiteSettings
        fields = "__all__"
        widgets = {
            "privacy_policy": CKEditor5Widget(config_name="default"),
            "cookie_policy": CKEditor5Widget(config_name="default"),
        }


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Синглтон: список сразу ведёт на единственную запись, удалить её нельзя."""

    form = SiteSettingsForm
    fieldsets = (
        ("Бренд", {"fields": ("brand", "tagline", "region_note")}),
        (
            "Контакты",
            {
                "fields": (
                    "phone_1",
                    "phone_2",
                    "email",
                    "viber_url",
                    "telegram_url",
                    "work_hours",
                    "address",
                    "youtube_url",
                )
            },
        ),
        ("Реквизиты", {"fields": ("legal_name", "unp", "accreditation", "accreditation_scan")}),
        ("Главная", {"fields": ("home_video_url", "home_video_preview", "online_service_url")}),
        ("Документы сайта", {"fields": ("privacy_policy", "privacy_updated_at", "cookie_policy")}),
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def changelist_view(
        self, request: HttpRequest, extra_context: Any = None
    ) -> HttpResponseRedirect:
        obj = SiteSettings.load()
        return HttpResponseRedirect(reverse("admin:core_sitesettings_change", args=[obj.pk]))


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "is_featured", "ordering")
    list_editable = ("is_featured", "ordering")
    search_fields = ("name",)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("author", "organization", "is_published", "ordering")
    list_editable = ("is_published", "ordering")


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "position", "is_published", "ordering")
    list_editable = ("is_published", "ordering")
