# apps/leads/forms.py — форма заявки с защитой от спама
"""
Форма заявки.

🔐 Защита: CSRF (Django), honeypot-поле ``website`` (люди его не видят, боты заполняют),
лимит частоты во view, проверка расширения, размера и сигнатуры файла, обязательное согласие на ПДн.
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from apps.leads.models import ALLOWED_ATTACHMENT_EXTENSIONS, Lead

PHONE_RE = re.compile(r"^\+?[\d\s()\-]{7,20}$")

# Первые байты разрешённых форматов: защита от переименованного исполняемого файла
MAGIC: dict[str, tuple[bytes, ...]] = {
    "pdf": (b"%PDF",),
    "png": (b"\x89PNG",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "docx": (b"PK\x03\x04",),
    "xlsx": (b"PK\x03\x04",),
    "doc": (b"\xd0\xcf\x11\xe0",),
    "xls": (b"\xd0\xcf\x11\xe0",),
}

SERVICE_CHOICES = [
    "Разработка СУОТ",
    "Документы по ОТ",
    "Обслуживание организации",
    "Аудит",
    "Выполнение предписания",
    "Консультация",
    "Другое",
]


class LeadForm(forms.ModelForm):
    """Заявка с сайта."""

    # Honeypot: скрыто стилями и aria-hidden; заполненное поле = бот
    website = forms.CharField(
        required=False,
        label="Сайт",
        widget=forms.TextInput(attrs={"autocomplete": "off", "tabindex": "-1"}),
    )
    consent = forms.BooleanField(
        required=True,
        label="Даю согласие на обработку персональных данных",
        error_messages={
            "required": "Без согласия на обработку персональных данных мы не можем принять заявку."
        },
    )
    source_url = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Lead
        fields: ClassVar[list[str]] = [
            "name",
            "phone",
            "email",
            "organization",
            "service",
            "headcount",
            "comment",
            "attachment",
            "consent",
            "source_url",
        ]
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "phone": forms.TextInput(
                attrs={"autocomplete": "tel", "inputmode": "tel", "placeholder": "+375"}
            ),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "organization": forms.TextInput(attrs={"autocomplete": "organization"}),
            "comment": forms.Textarea(attrs={"rows": 4}),
            "attachment": forms.ClearableFileInput(
                attrs={"accept": ",".join("." + e for e in ALLOWED_ATTACHMENT_EXTENSIONS)}
            ),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["name"].label = "Имя"
        self.fields["email"].label = "Эл. почта (необязательно)"
        self.fields["organization"].label = "Организация (необязательно)"
        self.fields["service"].label = "Что нужно"
        self.fields["headcount"].label = "Численность работников"
        self.fields["comment"].label = "Комментарий"
        self.fields["attachment"].label = "Штатное расписание или предписание (необязательно)"

    def clean_phone(self) -> str:
        phone = self.cleaned_data["phone"].strip()
        if not PHONE_RE.match(phone):
            raise forms.ValidationError("Укажите телефон в формате +375 29 123-45-67.")
        return phone

    def clean_name(self) -> str:
        name = self.cleaned_data["name"].strip()
        if "http" in name.lower() or "<" in name:
            raise forms.ValidationError("Укажите имя без ссылок и тегов.")
        return name

    def clean_attachment(self) -> UploadedFile | None:
        """Проверяет размер и реальный формат файла по первым байтам."""
        f = self.cleaned_data.get("attachment")
        if not f or not isinstance(f, UploadedFile):
            return f
        if f.size and f.size > settings.LEAD_ATTACHMENT_MAX_SIZE:
            mb = settings.LEAD_ATTACHMENT_MAX_SIZE // (1024 * 1024)
            raise forms.ValidationError(f"Файл больше {mb} МБ.")
        ext = (f.name or "").rsplit(".", 1)[-1].lower()
        head = f.read(8)
        f.seek(0)
        if ext not in MAGIC or not any(head.startswith(sig) for sig in MAGIC[ext]):
            raise forms.ValidationError(
                "Формат файла не поддерживается. Пришлите PDF, Word, Excel или фото."
            )
        return f

    @property
    def is_spam(self) -> bool:
        """Заполнено ли honeypot-поле."""
        return bool(self.data.get("website"))
