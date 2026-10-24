# apps/leads/models.py — заявки с сайта
from __future__ import annotations

from typing import ClassVar

from django.core.validators import FileExtensionValidator
from django.db import models

from apps.leads.storage import PrivateStorage, lead_upload_to

ALLOWED_ATTACHMENT_EXTENSIONS = ["pdf", "doc", "docx", "xls", "xlsx", "jpg", "jpeg", "png"]


class Lead(models.Model):
    """Заявка на расчёт или консультацию."""

    class Headcount(models.TextChoices):
        NONE = "", "Не указывать"
        UP_TO_15 = "lt15", "до 15"
        UP_TO_100 = "15-100", "15–100"
        UP_TO_500 = "100-500", "100–500"
        MORE = "gt500", "более 500"

    class Status(models.TextChoices):
        NEW = "new", "Новая"
        IN_WORK = "work", "В работе"
        DONE = "done", "Закрыта"
        SPAM = "spam", "Спам"

    name = models.CharField("Имя", max_length=150)
    phone = models.CharField("Телефон", max_length=30)
    email = models.EmailField("E-mail", blank=True)
    organization = models.CharField("Организация", max_length=255, blank=True)
    service = models.CharField("Что нужно", max_length=255, blank=True)
    headcount = models.CharField(
        "Численность", max_length=10, choices=Headcount.choices, blank=True
    )
    comment = models.TextField("Комментарий", blank=True, max_length=3000)
    attachment = models.FileField(
        "Файл",
        storage=PrivateStorage(),
        upload_to=lead_upload_to,
        blank=True,
        validators=[FileExtensionValidator(ALLOWED_ATTACHMENT_EXTENSIONS)],
    )
    attachment_name = models.CharField("Исходное имя файла", max_length=255, blank=True)
    consent = models.BooleanField("Согласие на обработку ПДн")
    source_url = models.CharField("Страница", max_length=500, blank=True)
    ip = models.GenericIPAddressField("IP", null=True, blank=True)
    user_agent = models.CharField("Браузер", max_length=300, blank=True)
    status = models.CharField("Статус", max_length=10, choices=Status.choices, default=Status.NEW)
    note = models.TextField("Заметка менеджера", blank=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering: ClassVar[list[str]] = ["-created_at"]

    def __str__(self) -> str:
        return (
            f"{self.name}, {self.phone} ({self.created_at:%d.%m.%Y %H:%M})"
            if self.created_at
            else self.name
        )
