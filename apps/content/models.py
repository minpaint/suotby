# apps/content/models.py — разделы, материалы, цены
"""
Контент сайта.

⚠️ Главное требование переезда — старые адреса. Поэтому у раздела и материала есть поле ``path``
с ПОЛНЫМ адресом страницы (``/slug.html``, ``/razdel/``, ``/pages/more-pages/…html``).
Маршрутизатор ищет страницу по ``path`` целиком, а не собирает адрес из частей — так сохраняются
и вложенные пути Joomla, и slug с точками или опечатками.
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import connection, models
from django.utils import timezone
from django.utils.html import strip_tags

from apps.core.sanitize import clean_html, clean_text

# Разрешённые символы адреса: латиница в нижнем регистре, цифры, дефис, точка, слеш
PATH_RE = re.compile(r"^/(?:[a-z0-9._\-]+/)*(?:[a-z0-9._\-]+\.html|[a-z0-9._\-]+/)?$")
slug_validator = RegexValidator(
    r"^[a-z0-9][a-z0-9._\-]*$", "Только латиница в нижнем регистре, цифры, дефис и точка."
)


def validate_path(value: str) -> None:
    """
    Проверяет полный адрес страницы.

    Args:
        value: адрес вида ``/slug.html`` или ``/razdel/``.

    Raises:
        ValidationError: если адрес не начинается со слеша или содержит недопустимые символы.
    """
    if not PATH_RE.match(value):
        raise ValidationError(
            "Адрес должен выглядеть как /slug.html или /razdel/ (латиница, цифры, дефис)."
        )


class Category(models.Model):
    """Раздел сайта: «Приказы по ОТ», подразделы «Вопрос-ответ», группы услуг."""

    class Kind(models.TextChoices):
        FAQ = "faq", "Вопрос-ответ"
        INSTRUCTIONS = "instructions", "Инструкции по ОТ"
        ORDERS = "orders", "Приказы по ОТ"
        RISK_CARDS = "risk_cards", "Карты рисков"
        ARTICLES = "articles", "Статьи"
        DOCUMENTS = "documents", "Нужные документы"
        SERVICES_OT = "services_ot", "Услуги по охране труда"
        SERVICES_SUOT = "services_suot", "Услуги по СУОТ"

    class Template(models.TextChoices):
        DEFAULT = "default", "Список материалов"
        FAQ_HUB = "faq_hub", "Хаб «Вопрос-ответ»"

    title = models.CharField("Название", max_length=255)
    slug = models.CharField("Slug", max_length=200, unique=True, validators=[slug_validator])
    path = models.CharField(
        "Адрес",
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        validators=[validate_path],
        help_text="Полный адрес раздела, например /prikazy-po-ohrane-truda/. Пусто — у раздела нет своей страницы.",
    )
    parent = models.ForeignKey(
        "self",
        verbose_name="Родитель",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
    )
    kind = models.CharField("Тип", max_length=20, choices=Kind.choices)
    template = models.CharField(
        "Шаблон", max_length=20, choices=Template.choices, default=Template.DEFAULT
    )
    description = models.TextField("Описание (HTML)", blank=True)
    menu_title = models.CharField("Короткое название для вкладок", max_length=100, blank=True)
    show_in_useful = models.BooleanField("Вкладка в «Полезное»", default=False)
    ordering = models.PositiveIntegerField("Порядок", default=0)
    meta_title = models.CharField("Title", max_length=255, blank=True)
    meta_description = models.CharField("Description", max_length=300, blank=True)
    legacy_id = models.CharField("ID в Joomla", max_length=30, blank=True, db_index=True)
    is_published = models.BooleanField("Опубликован", default=True)

    class Meta:
        verbose_name = "Раздел"
        verbose_name_plural = "Разделы"
        ordering: ClassVar[list[str]] = ["ordering", "title"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Чистит HTML описания перед сохранением."""
        self.description = clean_html(self.description)
        if self.path == "":
            self.path = None
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """Адрес раздела; для раздела без страницы — главная."""
        return self.path or "/"

    @property
    def short_title(self) -> str:
        """Название для вкладок «Полезное»."""
        return self.menu_title or self.title


class MaterialQuerySet(models.QuerySet["Material"]):
    """Частые выборки материалов."""

    def published(self) -> MaterialQuerySet:
        """Только опубликованные материалы с датой публикации не в будущем."""
        return self.filter(is_published=True, published_at__lte=timezone.now())


class Material(models.Model):
    """Любая страница-материал: услуга, статья, образец, вопрос, служебная страница."""

    class Type(models.TextChoices):
        SERVICE = "service", "Услуга"
        ARTICLE = "article", "Статья"
        DOCUMENT = "document", "Документ"
        INSTRUCTION = "instruction", "Инструкция по ОТ"
        ORDER_SAMPLE = "order_sample", "Образец приказа"
        RISK_CARD = "risk_card", "Карта рисков"
        FAQ = "faq", "Вопрос-ответ"
        REQUIREMENT = "requirement", "Требования ОТ (справка)"
        PAGE = "page", "Страница"

    class Template(models.TextChoices):
        AUTO = "auto", "По типу материала"
        SERVICES_HUB = "services_hub", "Все услуги"
        PRICES = "prices", "Цены"
        CONTACTS = "contacts", "Контакты"
        ABOUT = "about", "О нас"
        CLIENTS = "clients", "Наши клиенты"
        TERMS = "terms", "Условия и политика ПДн"
        SITEMAP = "sitemap", "Карта сайта"

    # Типы, которые показываются шаблоном «документ-образец»
    DOCUMENT_TYPES: ClassVar[set[str]] = {"document", "instruction", "order_sample", "risk_card"}
    # Типы, которые показываются шаблоном «вопрос»
    QUESTION_TYPES: ClassVar[set[str]] = {"faq", "requirement"}

    type = models.CharField("Тип", max_length=20, choices=Type.choices, db_index=True)
    template = models.CharField(
        "Шаблон страницы", max_length=20, choices=Template.choices, default=Template.AUTO
    )
    title = models.CharField("Заголовок", max_length=500)
    slug = models.CharField("Slug", max_length=255, unique=True, validators=[slug_validator])
    path = models.CharField(
        "Адрес",
        max_length=300,
        unique=True,
        blank=True,
        validators=[validate_path],
        help_text=(
            "Полный адрес. Пусто — /<slug>.html. "
            "⚠️ Не меняйте адрес у старых страниц: потеряются позиции в поиске."
        ),
    )
    category = models.ForeignKey(
        Category,
        verbose_name="Раздел",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="materials",
    )
    badge = models.CharField("Плашка над заголовком", max_length=100, blank=True)
    intro = models.TextField("Вводный текст (HTML)", blank=True)
    body = models.TextField("Основной текст (HTML)", blank=True)
    short_answer = models.TextField("«Коротко» — краткий ответ", blank=True)
    basis = models.TextField("Основание (НПА)", blank=True)
    price_from = models.DecimalField(
        "Цена от, BYN", max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_unit = models.CharField(
        "Единица цены", max_length=50, blank=True, help_text="например «/мес»"
    )
    file = models.FileField(
        "Файл для скачивания",
        upload_to="docs/",
        blank=True,
        validators=[FileExtensionValidator(["doc", "docx", "pdf", "xls", "xlsx", "odt"])],
    )
    file_pdf = models.FileField(
        "PDF-версия", upload_to="docs/", blank=True, validators=[FileExtensionValidator(["pdf"])]
    )
    cover = models.ImageField("Обложка", upload_to="covers/", blank=True)
    npa_checked_at = models.DateField("Ссылки на НПА проверены", null=True, blank=True)
    audit_flags = models.CharField("Что проверить по НПА", max_length=500, blank=True)
    related = models.ManyToManyField(
        "self", verbose_name="Связанные материалы", blank=True, symmetrical=False
    )
    is_featured = models.BooleanField("На главной", default=False)
    ordering = models.PositiveIntegerField("Порядок", default=0)

    meta_title = models.CharField("Title", max_length=255, blank=True)
    meta_description = models.CharField("Description", max_length=300, blank=True)
    meta_keywords = models.CharField("Keywords", max_length=500, blank=True)

    legacy_id = models.CharField("ID в Joomla", max_length=30, blank=True, db_index=True)
    legacy_url = models.CharField("Адрес в Joomla", max_length=500, blank=True)
    hits = models.PositiveIntegerField("Просмотры", default=0)
    rating_avg = models.DecimalField(
        "Оценка", max_digits=3, decimal_places=2, null=True, blank=True
    )
    rating_votes = models.PositiveIntegerField("Голосов", default=0)

    is_published = models.BooleanField("Опубликован", default=True)
    published_at = models.DateTimeField("Дата публикации", default=timezone.now)
    updated_at = models.DateTimeField("Обновлено", default=timezone.now)

    # Поиск: плоский текст без тегов и tsvector по нему (заполняются в save)
    search_text = models.TextField(editable=False, blank=True)
    search_vector = SearchVectorField(null=True, editable=False)

    objects = MaterialQuerySet.as_manager()

    class Meta:
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"
        ordering: ClassVar[list[str]] = ["ordering", "title"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["type", "is_published"]),
            models.Index(fields=["-hits"]),
            GinIndex(fields=["search_vector"]),
        ]

    def __str__(self) -> str:
        return self.title

    # ------------------------------------------------------------------ сохранение
    def clean(self) -> None:
        """Проверяет, что адрес не занят разделом."""
        path = self.path or f"/{self.slug}.html"
        if Category.objects.filter(path=path).exists():
            raise ValidationError({"path": "Этот адрес уже занят разделом."})

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Перед сохранением: адрес по умолчанию, санитайзер HTML, текст для поиска.
        После сохранения: пересчёт tsvector (только PostgreSQL).
        """
        if not self.path:
            self.path = f"/{self.slug}.html"
        self.intro = clean_html(self.intro)
        self.body = clean_html(self.body)
        self.basis = clean_html(self.basis)
        self.short_answer = clean_text(self.short_answer)
        self.search_text = clean_text(strip_tags(f"{self.intro} {self.body}"))
        super().save(*args, **kwargs)
        if connection.vendor == "postgresql":
            # 💡 русская морфология: «инструктаж», «инструктажи», «инструктажа» найдутся одним запросом
            Material.objects.filter(pk=self.pk).update(
                search_vector=SearchVector("title", weight="A", config="russian")
                + SearchVector("search_text", weight="B", config="russian")
            )

    def get_absolute_url(self) -> str:
        """Полный адрес материала (старый адрес сохраняется как есть)."""
        return self.path

    # ------------------------------------------------------------------ для шаблонов
    @property
    def is_document(self) -> bool:
        """Показывать шаблоном «документ-образец»."""
        return self.type in self.DOCUMENT_TYPES

    @property
    def is_question(self) -> bool:
        """Показывать шаблоном «вопрос»."""
        return self.type in self.QUESTION_TYPES

    @property
    def file_ext(self) -> str:
        """Расширение файла для кнопки «Скачать .docx»."""
        return (self.file.name or "").rsplit(".", 1)[-1].lower() if self.file else ""

    @property
    def reading_minutes(self) -> int:
        """Примерное время чтения (180 слов в минуту)."""
        return max(1, round(len(self.search_text.split()) / 180))

    @property
    def seo_title(self) -> str:
        """Title страницы."""
        return self.meta_title or self.title


class ServiceFAQ(models.Model):
    """Вопрос-ответ под конкретной услугой (аккордеон «Частые вопросы по услуге»)."""

    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name="service_faqs")
    question = models.CharField("Вопрос", max_length=300)
    answer = models.TextField("Ответ (HTML)")
    ordering = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Вопрос по услуге"
        verbose_name_plural = "Вопросы по услуге"
        ordering: ClassVar[list[str]] = ["ordering", "id"]

    def __str__(self) -> str:
        return self.question

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.answer = clean_html(self.answer)
        super().save(*args, **kwargs)


class PriceItem(models.Model):
    """Позиция на странице «Цены»: тариф-карточка или строка таблицы."""

    class Kind(models.TextChoices):
        TARIFF = "tariff", "Тариф (карточка)"
        ROW = "row", "Строка таблицы"

    kind = models.CharField("Вид", max_length=10, choices=Kind.choices, default=Kind.ROW)
    title = models.CharField("Услуга", max_length=255)
    unit = models.CharField("Единица", max_length=100, blank=True)
    price = models.CharField(
        "Цена, BYN", max_length=50, blank=True, help_text="Например «от 300» или «по запросу»"
    )
    description = models.CharField("Описание", max_length=300, blank=True)
    term = models.CharField("Срок", max_length=100, blank=True)
    badge = models.CharField("Плашка", max_length=50, blank=True)
    is_highlighted = models.BooleanField("Выделить", default=False)
    service = models.ForeignKey(
        Material,
        verbose_name="Услуга на сайте",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"type": "service"},
    )
    show_on_home = models.BooleanField("Показывать на главной", default=False)
    ordering = models.PositiveIntegerField("Порядок", default=0)
    is_published = models.BooleanField("Опубликован", default=True)

    class Meta:
        verbose_name = "Цена"
        verbose_name_plural = "Цены"
        ordering: ClassVar[list[str]] = ["kind", "ordering", "id"]

    def __str__(self) -> str:
        return self.title
