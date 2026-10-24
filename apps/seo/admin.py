# apps/seo/admin.py — переадресации и 410 в админке
from django.contrib import admin

from apps.seo.models import Gone, Redirect


@admin.register(Redirect)
class RedirectAdmin(admin.ModelAdmin):
    list_display = ("old_path", "new_path", "code", "note")
    list_filter = ("code",)
    search_fields = ("old_path", "new_path", "note")


@admin.register(Gone)
class GoneAdmin(admin.ModelAdmin):
    list_display = ("path", "note")
    search_fields = ("path",)
