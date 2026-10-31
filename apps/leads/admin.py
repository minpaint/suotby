# apps/leads/admin.py — заявки в админке
from __future__ import annotations

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from apps.leads.models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("created_at", "name", "phone", "service", "headcount", "status", "has_file")
    list_filter = ("status", "service", "headcount", "created_at")
    list_editable = ("status",)
    search_fields = ("name", "phone", "email", "organization", "comment")
    readonly_fields = (
        "name",
        "phone",
        "email",
        "organization",
        "service",
        "headcount",
        "comment",
        "file_link",
        "consent",
        "source_url",
        "ip",
        "user_agent",
        "created_at",
    )
    fields = ("status", "note", *readonly_fields)
    date_hierarchy = "created_at"

    @admin.display(description="Файл", boolean=True)
    def has_file(self, obj: Lead) -> bool:
        return bool(obj.attachment)

    @admin.display(description="Вложение")
    def file_link(self, obj: Lead) -> str:
        if not obj.attachment:
            return "—"
        url = reverse("lead_attachment", args=[obj.pk])
        return format_html('<a href="{}">Скачать</a>', url)

    def has_add_permission(self, request: object) -> bool:
        return False
