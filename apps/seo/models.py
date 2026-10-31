# apps/seo/models.py — переадресации и удалённые адреса
from __future__ import annotations

from typing import ClassVar

from django.db import models


class Redirect(models.Model):
    """Переадресация со старого адреса (точное совпадение пути)."""

    class Code(models.IntegerChoices):
        PERMANENT = 301, "301 — навсегда"
        TEMPORARY = 302, "302 — временно"

    old_path = models.CharField(
        "Старый адрес",
        max_length=500,
        unique=True,
        help_text="Путь без домена, например /about.html",
    )
    new_path = models.CharField("Новый адрес", max_length=500)
    code = models.PositiveSmallIntegerField("Код", choices=Code.choices, default=Code.PERMANENT)
    note = models.CharField("Комментарий", max_length=300, blank=True)
    hits = models.PositiveIntegerField("Срабатываний", default=0)

    class Meta:
        verbose_name = "Переадресация"
        verbose_name_plural = "Переадресации"
        ordering: ClassVar[list[str]] = ["old_path"]

    def __str__(self) -> str:
        return f"{self.old_path} → {self.new_path}"


class Gone(models.Model):
    """Адрес, удалённый навсегда: отвечает 410, чтобы поисковики быстрее убрали его из индекса."""

    path = models.CharField("Адрес", max_length=500, unique=True)
    note = models.CharField("Комментарий", max_length=300, blank=True)

    class Meta:
        verbose_name = "Удалённый адрес (410)"
        verbose_name_plural = "Удалённые адреса (410)"
        ordering: ClassVar[list[str]] = ["path"]

    def __str__(self) -> str:
        return self.path
