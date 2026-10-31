# apps/leads/storage.py — закрытое хранилище вложений заявок
"""
🔐 Вложения заявок (штатные расписания, предписания) — персональные и коммерческие данные.

Они хранятся в ``PRIVATE_MEDIA_ROOT`` (вне папки, которую раздаёт Nginx), под случайными
именами, и отдаются только сотрудникам через админку.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateStorage(FileSystemStorage):
    """Файловое хранилище без публичного URL."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(location=str(settings.PRIVATE_MEDIA_ROOT), base_url=None, **kwargs)


def lead_upload_to(instance: Any, filename: str) -> str:
    """
    Случайное имя файла с сохранением расширения: исходное имя не попадает на диск.

    Args:
        instance: заявка (не используется).
        filename: имя файла от пользователя.

    Returns:
        Относительный путь ``leads/ГГГГ/ММ/<uuid>.<ext>``.
    """
    from django.utils import timezone

    ext = Path(filename).suffix.lower()[:10]
    now = timezone.now()
    return f"leads/{now:%Y/%m}/{uuid.uuid4().hex}{ext}"
