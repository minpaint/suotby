# apps/content/importer.py — импорт выгрузки старого сайта (content/*.md) в базу
"""
Импорт контента Joomla из выгрузки ``export_content.py`` (см. CLAUDE.md, раздел 3).

Файл материала: YAML-шапка между ``---`` и тело в Markdown (таблицы — чистый HTML),
``<!-- readmore -->`` отделяет вводный текст.

Принципы:

* ✅ идемпотентно — повторный запуск обновляет материалы по ``legacy_id``, не дублирует;
* ⚠️ старый адрес (``url``) сохраняется как ``path`` без изменений, кроме очевидно битых символов;
* 🔐 весь HTML проходит санитайзер (в ``Material.save``);
* мусор конструктора страниц (кнопки «ОТПРАВИТЬ ЗАЯВКУ», телефоны, картинка consult.png) вырезается —
  на новом сайте эти блоки рисует шаблон.
"""

from __future__ import annotations

import logging
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import markdown
import yaml
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.content.models import PATH_RE, Category, Material
from apps.content.services import SPECIAL_PAGE_TEMPLATES
from apps.content.structure import USEFUL

logger = logging.getLogger("apps.content.import")

# Папки выгрузки, которые на новый сайт не переносятся
SKIP_DIRS = {"_korzina", "stranicy-shablona", "sluzhebnye", "_media"}
# Материалы без адреса со старыми контактами ПрофиТруда — не использовать (CLAUDE.md, раздел 3)
SKIP_IDS = {"40", "41"}

TYPE_MAP: dict[str, str] = {
    "вопрос-ответ": Material.Type.FAQ,
    "услуга": Material.Type.SERVICE,
    "статья": Material.Type.ARTICLE,
    "инструкция по ОТ": Material.Type.INSTRUCTION,
    "карта рисков": Material.Type.RISK_CARD,
    "образец приказа": Material.Type.ORDER_SAMPLE,
    "документ": Material.Type.DOCUMENT,
    "страница": Material.Type.PAGE,
    "страница конструктора": Material.Type.PAGE,
}

FOLDER_TO_CATEGORY: dict[str, str] = {d["folder"]: d["slug"] for d in USEFUL}

# Начало «хвоста» конструктора страниц: всё от этого места до конца — служебные кнопки и телефоны
_CTA_TAIL_RE = re.compile(
    r"(Оставьте заявку, задайте вопрос|#{2,3}\s*\**Бесплатная консультация|Задать вопрос по услуге)",
    re.IGNORECASE,
)
_JUNK_LINES_RE = re.compile(
    r"^\s*(Button Text|ОТПРАВИТЬ ЗАЯВКУ!?|#+\s*Executive Board|#+\s*Meet Our Consultants|"
    r"!\[[^\]]*\]\(/images/2021/02/07/consult\.png\))\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_SHORTCODE_RE = re.compile(r"\{[a-z0-9_]+[^{}]*\}", re.IGNORECASE)  # {loadposition …}, {sh404sef…}
_IFRAME_RE = re.compile(r"<iframe.*?</iframe>", re.IGNORECASE | re.DOTALL)
_IMG_RE = re.compile(
    r"""(src|href)=(["'])(?:https?://(?:www\.)?suot\.by)?/(images/[^"']+)\2""", re.IGNORECASE
)
_SELF_LINK_RE = re.compile(r"""href=(["'])https?://(?:www\.)?suot\.by(/[^"']*)\1""", re.IGNORECASE)
_BAD_PATH_CHARS = re.compile(r"[^a-z0-9._/\-]")


@dataclass
class ImportReport:
    """Итоги импорта для вывода в консоль."""

    created: int = 0
    updated: int = 0
    categories: int = 0
    skipped: list[str] = field(default_factory=list)
    fixed_paths: list[str] = field(default_factory=list)
    missing_media: set[str] = field(default_factory=set)
    copied_media: int = 0
    by_type: dict[str, int] = field(default_factory=dict)

    def lines(self) -> list[str]:
        """Текст отчёта построчно."""
        out = [
            f"Создано материалов: {self.created}",
            f"Обновлено материалов: {self.updated}",
            f"Разделов привязано: {self.categories}",
            "По типам: " + ", ".join(f"{k}={v}" for k, v in sorted(self.by_type.items())),
            f"Скопировано картинок/файлов: {self.copied_media}",
            f"Пропущено: {len(self.skipped)}",
        ]
        out += [f"  — {s}" for s in self.skipped]
        if self.fixed_paths:
            out.append(f"Исправлено адресов: {len(self.fixed_paths)}")
            out += [f"  — {s}" for s in self.fixed_paths]
        if self.missing_media:
            out.append(f"⚠️ Нет файлов в _media: {len(self.missing_media)}")
            out += [f"  — {s}" for s in sorted(self.missing_media)[:50]]
        return out


def parse_md(path: Path) -> tuple[dict[str, Any], str]:
    """
    Читает файл выгрузки.

    Args:
        path: путь к ``.md``.

    Returns:
        ``(шапка, тело)``; при отсутствии шапки — ``({}, весь текст)``.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    _, head, body = text.split("---", 2)
    meta = yaml.safe_load(head) or {}
    return meta, body.lstrip("\n")


def normalize_path(url: str) -> str:
    """
    Приводит старый адрес к допустимому виду, НЕ меняя нормальные адреса.

    Битые символы (длинное тире, кириллица) вырезаются, двойные дефисы схлопываются:
    ``/razrabotka-…-–-eto-obyazatelno.html`` → ``/razrabotka-…-eto-obyazatelno.html``
    (так и записано в redirects.csv).

    Args:
        url: адрес из выгрузки.

    Returns:
        Путь, проходящий :data:`PATH_RE`.
    """
    path = url.strip()
    if PATH_RE.match(path):
        return path
    path = _BAD_PATH_CHARS.sub("", path.lower())
    path = re.sub(r"-{2,}", "-", path)
    return path


def clean_body(md_text: str, *, strip_cta: bool) -> str:
    """
    Убирает мусор Joomla из Markdown.

    Args:
        md_text: исходный текст.
        strip_cta: срезать «хвост» конструктора (кнопки, телефоны) — для страниц Page Builder.

    Returns:
        Очищенный Markdown.
    """
    text = _IFRAME_RE.sub("", md_text)
    text = _SHORTCODE_RE.sub("", text)
    text = _JUNK_LINES_RE.sub("", text)
    if strip_cta:
        m = _CTA_TAIL_RE.search(text)
        if m:
            text = text[: m.start()]
    return text.strip()


def md_to_html(md_text: str) -> str:
    """Markdown → HTML (сырые HTML-таблицы проходят как есть; санитайзер — в Material.save)."""
    return markdown.markdown(md_text, extensions=["tables", "sane_lists"], output_format="html")


def _parse_dt(value: Any) -> datetime | None:
    """Дата из шапки ('2022-10-22 15:52:12') в aware datetime."""
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.strptime(str(value)[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


class JoomlaImporter:
    """Импортирует папку выгрузки ``content/``."""

    def __init__(self, source: Path, *, copy_media: bool = True) -> None:
        """
        Args:
            source: папка ``content`` выгрузки (с подпапками разделов и ``_media``).
            copy_media: копировать ли картинки из ``_media`` в ``MEDIA_ROOT/legacy``.
        """
        self.source = source
        self.media_src = source / "_media"
        self.media_dst = Path(settings.MEDIA_ROOT) / "legacy"
        self.copy_media = copy_media
        self.report = ImportReport()
        self.categories_by_legacy = {c.legacy_id: c for c in Category.objects.exclude(legacy_id="")}
        self.categories_by_slug = {c.slug: c for c in Category.objects.all()}
        self.categories_by_kind = {c.kind: c for c in Category.objects.filter(path__isnull=True)}

    # ------------------------------------------------------------------ обход
    def files(self) -> list[Path]:
        """Все .md выгрузки, кроме служебных папок; ``_index.md`` — первыми."""
        result: list[Path] = []
        for p in sorted(self.source.rglob("*.md")):
            rel = p.relative_to(self.source)
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            if p.name.startswith("_") and p.name != "_index.md":
                continue
            if p.parent == self.source:  # README.md, отчёты в корне выгрузки
                continue
            result.append(p)
        return sorted(result, key=lambda p: (p.name != "_index.md", str(p)))

    def run(self) -> ImportReport:
        """Импортирует всё. Returns: отчёт."""
        for path in self.files():
            meta, body = parse_md(path)
            rel = str(path.relative_to(self.source))
            if path.name == "_index.md":
                self.import_category(meta)
            else:
                with transaction.atomic():
                    self.import_material(meta, body, rel)
        return self.report

    # ------------------------------------------------------------------ разделы
    def import_category(self, meta: dict[str, Any]) -> None:
        """Привязывает раздел «Вопрос-ответ» из ``_index.md`` к существующему по адресу."""
        url = meta.get("url")
        if not url:
            return
        cat = Category.objects.filter(path=url).first()
        if cat is None:
            self.report.skipped.append(
                f"раздел {meta.get('id')} {url}: нет в структуре (seed_site)"
            )
            return
        cat.legacy_id = str(meta.get("id", cat.legacy_id))
        cat.save(update_fields=["legacy_id"])
        self.categories_by_legacy[cat.legacy_id] = cat
        self.report.categories += 1

    def category_for(self, meta: dict[str, Any], rel: str) -> Category | None:
        """Раздел материала: по номеру категории «Вопрос-ответ», по папке или по группе услуг."""
        section = str(meta.get("section", ""))
        top = rel.replace("\\", "/").split("/")[0]
        if section.startswith("vopros-otvet/"):
            num = section.split("/")[1].split("-")[0]
            return self.categories_by_legacy.get(f"cat-{num}")
        if top in FOLDER_TO_CATEGORY:
            return self.categories_by_slug.get(FOLDER_TO_CATEGORY[top])
        if meta.get("type") == "услуга":
            kind = (
                Category.Kind.SERVICES_SUOT
                if "СУОТ" in str(meta.get("category", ""))
                else Category.Kind.SERVICES_OT
            )
            return self.categories_by_kind.get(kind)
        return None

    # ------------------------------------------------------------------ материалы
    def import_material(self, meta: dict[str, Any], body: str, rel: str) -> None:
        """Создаёт или обновляет один материал."""
        legacy_id = str(meta.get("id", "")).strip()
        url = meta.get("url")
        if not legacy_id or legacy_id in SKIP_IDS:
            self.report.skipped.append(f"{rel}: служебный или старый материал (id {legacy_id})")
            return
        # ✏️ ИЗМЕНЕНО: услуга id 34 лежала в Joomla в Uncategorised и выгрузилась как страница.
        # 💡 Исправляем классификацию при каждом импорте, сохраняя основной адрес и текст.
        if legacy_id == "34":
            meta = {**meta, "type": "услуга", "category": "Услуги по охране труда"}
        if not url:
            self.report.skipped.append(f"{rel}: нет адреса на сайте")
            return
        if url == "/":
            self.report.skipped.append(f"{rel}: главная — собрана шаблоном pages/home.html")
            return
        path = normalize_path(str(url))
        if path != url:
            self.report.fixed_paths.append(f"{url} → {path}")

        mtype = TYPE_MAP.get(str(meta.get("type", "")), Material.Type.PAGE)
        if mtype == Material.Type.FAQ and path.startswith("/ohrana-truda-pri-"):
            mtype = Material.Type.REQUIREMENT
        is_builder = str(meta.get("source", "")) == "page builder"

        parts = re.split(r"<!--\s*readmore\s*-->", body, maxsplit=1)
        intro_md, body_md = (parts[0], parts[1]) if len(parts) == 2 else ("", parts[0])
        strip_cta = is_builder or mtype in (Material.Type.SERVICE, Material.Type.PAGE)
        intro_html = self.fix_links(md_to_html(clean_body(intro_md, strip_cta=False)))
        body_html = self.fix_links(md_to_html(clean_body(body_md, strip_cta=strip_cta)))

        obj = Material.objects.filter(legacy_id=legacy_id).first()
        if obj is None:
            obj = Material.objects.filter(path=path).first()  # служебная страница из seed_site
        created = obj is None
        if obj is None:
            obj = Material(legacy_id=legacy_id)

        obj.legacy_id = legacy_id
        obj.legacy_url = str(url)
        obj.path = path
        obj.slug = self.unique_slug(path, obj.pk, legacy_id)
        obj.title = str(meta.get("title", "")).strip().rstrip(":")[:500]
        obj.type = mtype
        if path in SPECIAL_PAGE_TEMPLATES:
            obj.template = SPECIAL_PAGE_TEMPLATES[path]
        obj.category = self.category_for(meta, rel) or obj.category
        obj.intro = intro_html
        obj.body = body_html
        obj.meta_description = str(meta.get("description") or "")[:300]
        obj.meta_keywords = str(meta.get("keywords") or "")[:500]
        obj.audit_flags = str(meta.get("audit_flags") or "")[:500]
        obj.hits = int(meta.get("hits") or meta.get("traffic_sh404sef") or 0)
        rating = meta.get("rating") or {}
        if isinstance(rating, dict) and rating.get("votes"):
            try:
                obj.rating_avg = Decimal(str(rating.get("avg")))
            except InvalidOperation:
                obj.rating_avg = None
            obj.rating_votes = int(rating["votes"])
        obj.published_at = _parse_dt(meta.get("created")) or obj.published_at or timezone.now()
        obj.updated_at = _parse_dt(meta.get("modified")) or obj.published_at
        obj.is_published = True
        images = meta.get("images") or {}
        cover = (
            (images.get("fulltext") or images.get("intro")) if isinstance(images, dict) else None
        )
        if cover and mtype == Material.Type.ARTICLE:
            name = self.copy_file(str(cover))
            if name:
                obj.cover.name = name
        obj.save()

        self.report.by_type[mtype] = self.report.by_type.get(mtype, 0) + 1
        if created:
            self.report.created += 1
        else:
            self.report.updated += 1

    def unique_slug(self, path: str, pk: int | None, legacy_id: str) -> str:
        """Slug из последней части адреса; при совпадении с другим материалом — с суффиксом id."""
        slug = path.strip("/").removesuffix(".html").split("/")[-1] or f"material-{legacy_id}"
        slug = slug.strip(".-") or f"material-{legacy_id}"
        clash = Material.objects.filter(slug=slug)
        if pk:
            clash = clash.exclude(pk=pk)
        return f"{slug}-{legacy_id}" if clash.exists() else slug

    # ------------------------------------------------------------------ ссылки и файлы
    def fix_links(self, html: str) -> str:
        """
        Переписывает ссылки: ``/images/…`` → ``/media/legacy/images/…`` (с копированием файла),
        абсолютные ссылки на suot.by → относительные.
        """

        def repl_img(m: re.Match[str]) -> str:
            attr, quote, rel = m.group(1), m.group(2), m.group(3)
            name = self.copy_file("/" + rel)
            url = settings.MEDIA_URL + name if name else "/" + rel
            return f"{attr}={quote}{url}{quote}"

        html = _IMG_RE.sub(repl_img, html)
        # alt="Image" — подпись по умолчанию из SP Page Builder, для читалок экрана это шум
        html = html.replace('alt="Image"', 'alt=""')
        return _SELF_LINK_RE.sub(lambda m: f"href={m.group(1)}{m.group(2)}{m.group(1)}", html)

    def copy_file(self, src_url: str) -> str | None:
        """
        Копирует файл из ``_media`` в ``MEDIA_ROOT/legacy``.

        Args:
            src_url: адрес на старом сайте (``/images/a.jpg``).

        Returns:
            Имя файла относительно ``MEDIA_ROOT`` или None, если файла нет в выгрузке.
        """
        rel = src_url.split("?")[0].lstrip("/")
        if ".." in rel:  # 🔐 защита от выхода за пределы папки
            return None
        src = self.media_src / rel
        if not src.is_file():
            self.report.missing_media.add(rel)
            return None
        if self.copy_media:
            dst = self.media_dst / rel
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                self.report.copied_media += 1
        return f"legacy/{rel}"
