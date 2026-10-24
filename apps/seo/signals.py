# apps/seo/signals.py — сброс кэша таблиц переадресаций при изменениях
from __future__ import annotations

from typing import Any

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.seo.models import Gone, Redirect
from apps.seo.services import reset_maps


@receiver([post_save, post_delete], sender=Redirect)
@receiver([post_save, post_delete], sender=Gone)
def _reset(**kwargs: Any) -> None:
    """После правки переадресации — новые правила действуют сразу."""
    reset_maps()
