# apps/core/models.py — настройки сайта, клиенты, отзывы, команда
"""
Модели «общих модулей» сайта.

* :class:`SiteSettings` — синглтон с контактами и реквизитами (шапка, подвал, контакты, условия).
* :class:`Client`, :class:`Testimonial`, :class:`TeamMember` — блоки «Нам доверяют», отзывы, команда.

💡 Пустые поля не подменяются выдуманными значениями: шаблон просто не показывает блок.
"""

from __future__ import annotations

from typing import Any, ClassVar

from django.core.cache import cache
from django.db import models

from apps.core.sanitize import clean_html

SETTINGS_CACHE_KEY = "core:site_settings"


class SiteSettings(models.Model):
    """Контакты, реквизиты и тексты служебных страниц. В базе всегда одна запись (pk=1)."""

    brand = models.CharField("Название бренда", max_length=100, default="СУОТ.BY")
    tagline = models.CharField(
        "Подпись",
        max_length=200,
        default="Разработка СУОТ и услуги по охране труда в Минске и по всей Беларуси",
    )
    region_note = models.CharField(
        "География (верхняя полоса)",
        max_length=200,
        default="Минск и вся Беларусь · выезд и удалённо",
    )
    phone_1 = models.CharField("Телефон 1", max_length=30, default="+375 (29) 35-70-911")
    phone_2 = models.CharField("Телефон 2", max_length=30, blank=True, default="+375 (33) 35-70-911")
    email = models.EmailField("E-mail", blank=True, default="3570911@tut.by")
    viber_url = models.CharField(
        "Ссылка Viber", max_length=200, blank=True, default="viber://chat?number=%2B375293570911"
    )
    telegram_url = models.CharField(
        "Ссылка Telegram", max_length=200, blank=True, default="https://t.me/+375293570911"
    )
    youtube_url = models.URLField(
        "Канал YouTube",
        blank=True,
        default="https://www.youtube.com/channel/UCGdkOs-3DE-mGvtmFkq-oUA",
    )
    work_hours = models.CharField("Часы работы", max_length=100, blank=True)
    address = models.CharField("Адрес для корреспонденции", max_length=255, blank=True)

    legal_name = models.CharField("Исполнитель услуг", max_length=200, default="ИП Мингинович А.Г.")
    unp = models.CharField("УНП", max_length=20, default="192308594")
    accreditation = models.CharField(
        "Свидетельство об аккредитации (номер, дата, срок)", max_length=255, blank=True
    )
    accreditation_scan = models.ImageField("Скан аккредитации", upload_to="site/", blank=True)

    home_video_url = models.URLField(
        "Видео на главной", blank=True, default="https://www.youtube.com/watch?v=ccLVYIBhMCU"
    )
    home_video_preview = models.ImageField("Превью видео", upload_to="site/", blank=True)
    online_service_url = models.URLField("Ссылка на онлайн-сервис учёта по ОТ", blank=True)

    privacy_policy = models.TextField(
        "Политика обработки персональных данных (HTML)",
        blank=True,
        help_text="⚠️ Обязательна до запуска форм (Закон РБ «О защите персональных данных»).",
    )
    cookie_policy = models.TextField("Политика cookie (HTML)", blank=True)
    privacy_updated_at = models.DateField("Редакция политики от", null=True, blank=True)

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self) -> str:
        return "Настройки сайта"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Держит единственную запись (pk=1), чистит HTML политик и сбрасывает кэш."""
        self.pk = 1
        self.privacy_policy = clean_html(self.privacy_policy)
        self.cookie_policy = clean_html(self.cookie_policy)
        super().save(*args, **kwargs)
        cache.delete(SETTINGS_CACHE_KEY)

    @classmethod
    def load(cls) -> SiteSettings:
        """
        Возвращает настройки (из кэша), создавая запись по умолчанию при первом обращении.

        Returns:
            Экземпляр :class:`SiteSettings`.
        """
        obj = cache.get(SETTINGS_CACHE_KEY)
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            cache.set(SETTINGS_CACHE_KEY, obj, 3600)
        return obj

    @property
    def phones(self) -> list[str]:
        """Непустые телефоны по порядку."""
        return [p for p in (self.phone_1, self.phone_2) if p]

    @staticmethod
    def tel_href(phone: str) -> str:
        """Превращает «+375 29 357-09-11» в «tel:+375293570911»."""
        return "tel:" + "".join(ch for ch in phone if ch.isdigit() or ch == "+")


class Client(models.Model):
    """Организация-клиент для страницы «Наши клиенты» и блока «Нам доверяют»."""

    name = models.CharField("Название", max_length=255)
    is_featured = models.BooleanField("Показывать в «Нам доверяют»", default=False)
    logo = models.ImageField("Логотип", upload_to="clients/", blank=True)
    ordering = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering: ClassVar[list[str]] = ["ordering", "id"]

    def __str__(self) -> str:
        return self.name


class Testimonial(models.Model):
    """Отзыв клиента. Публикуется только реальный отзыв с разрешения клиента."""

    text = models.TextField("Текст отзыва")
    author = models.CharField("Имя, должность", max_length=200)
    organization = models.CharField("Организация", max_length=200, blank=True)
    scan = models.FileField("Скан письма", upload_to="testimonials/", blank=True)
    is_published = models.BooleanField("Опубликован", default=False)
    ordering = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering: ClassVar[list[str]] = ["ordering", "-id"]

    def __str__(self) -> str:
        return f"{self.author} — {self.organization}".strip(" —")


class TeamMember(models.Model):
    """Сотрудник для блока «Команда» на странице «О нас»."""

    name = models.CharField("Имя и фамилия", max_length=150)
    position = models.CharField("Должность, опыт, аттестация", max_length=255, blank=True)
    photo = models.ImageField("Фото", upload_to="team/", blank=True)
    is_published = models.BooleanField("Опубликован", default=True)
    ordering = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Команда"
        ordering: ClassVar[list[str]] = ["ordering", "id"]

    def __str__(self) -> str:
        return self.name
