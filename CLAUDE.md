# CLAUDE.md — suot.by на Django

> **Статус (24.10.2026):** реализованы шаги 1–7 раздела 11 в ветке `feature/site` — модели, админка, импорт,
> шаблоны по всем макетам, формы, SEO, тесты (покрытие 97%), Docker, CI, конфиги деплоя (`deploy/`, `docs/deploy.md`).
> Осталось: прогнать `import_joomla` на полной выгрузке и `check_legacy_urls`, заполнить открытые вопросы (раздел 12).

Этот файл — техническое задание и правила работы для Claude Code в репозитории `minpaint/suotby`.
Читай его целиком перед любой задачей. Отвечай и пиши комментарии **на русском**.

## 1. Цель

Перевести сайт **suot.by** (услуги по охране труда и разработке СУОТ, Минск и Беларусь) с Joomla 4 + SP Page Builder
на **Python / Django** по готовым макетам, **не потеряв адреса и позиции в поиске**.

- Владелец бренда: «СУОТ.BY» — торговая марка, не юрлицо. Услуги оказывает **ИП Мингинович А.Г., УНП 192308594**.
- Телефоны: +375 29 357-09-11, +375 33 357-09-11 (Viber, Telegram). E-mail: 3570911@tut.by (⚠️ уточнить актуальность).

## 2. Что уже есть

| Что | Где |
|---|---|
| Макеты 17 страниц (дизайн-источник) | `docs/mockups/*.dc.html`, раскладка — `docs/mockups/canvas.json` |
| Список всех 280 материалов старого сайта (id, title, url, тип, раздел, слова, трафик, файл) | `docs/data/content_manifest.json` |
| Таблица адресов старого сайта: что сохранить (keep), куда 301, что 410 | `docs/data/redirects.csv` (разделитель `;`) |
| Полная выгрузка контента (`.md` с YAML-шапкой), картинки `_media/` | Google Диск: `coding/suot.by/content/` — **в репозиторий не положена, попросить у пользователя** |
| Исходная БД Joomla, сконвертированная в SQLite (дамп от 11.09.2025) | Google Диск: `coding/suot.by/data/old_site.sqlite` (33 МБ) |
| Аудит текстов (ссылки на НПА, флаги) | Google Диск: `coding/suot.by/audit/` (`pages.csv`, `npa.csv`, `links.csv`) |
| Скрипты, которыми делалась выгрузка | Google Диск: `coding/suot.by/tools/` (`export_content.py`, `verify_export.py`, `sql_to_sqlite.py`) |

⚠️ Данные с Диска нужно получить от пользователя (подключённая папка или архив). Положи их в `data/` (в `.gitignore`), **не коммить** выгрузку, БД и картинки.

### О макетах `.dc.html`
Это HTML с инлайн-стилями для дизайн-холста: разметка внутри `<x-dc>…</x-dc>`, данные списков — в `renderVals()`
скрипта `text/x-dc`, `{{...}}` — подстановки, `<sc-for>` — цикл, `<dc-import name="Shapka">` — подключение
модуля шапки/подвала. **Не запускай их как есть** — используй как точный эталон структуры, текстов, отступов и цветов
и переводи в шаблоны Django + общий CSS.

## 3. Формат выгрузки контента

Каждый материал — файл `content/<раздел>/<id>-<slug>.md`:

```markdown
---
id: 188                     # id материала Joomla (pb-N — страница SP Page Builder, cat-N — раздел)
title: …
url: /v-kakih-sluchayah-….html   # СТАРЫЙ адрес — сохранить на новом сайте
type: вопрос-ответ          # см. таблицу типов ниже
section: vopros-otvet/34-organizaciya-raboty-po-ohrane-truda
category: Организация работы по охране труда
created / modified: '2022-10-22 15:52:12'
description / keywords: …   # meta, если были
images: {intro, fulltext}
hits: 29457                 # просмотры Joomla
traffic_sh404sef: 29455
rating: {avg, votes}
source: материал | page builder
words: 1609
audit_flags: пост. № 175 (обучение)   # что проверить по НПА
---

Вводный текст…

<!-- readmore -->

Основной текст в Markdown; таблицы — чистый HTML.
```

Разделы выгрузки: `vopros-otvet/<id>-<раздел>/` (201 вопрос в 13 подразделах, у каждого `_index.md`), `uslugi/` (17),
`instrukcii/` (10), `karty-riskov/` (10), `prikazy/` (6), `stati/` (13), `nuzhnye-dokumenty/` (1), `stranicy/` (14),
`glavnaya/` (1), `stranicy-shablona/` (4 — на новый сайт не переносить, 301 → `/o-nas.html`), `sluzhebnye/` (404),
`_korzina/` (2 — не публиковать).

Известные особенности выгрузки (из `_export_report.md`):
- У 15 услуг текст на сайте шёл из SP Page Builder; в выгрузке — именно он. Под ним в БД лежал старый текст статьи — **не переносить**.
- Ссылки на картинки — `/images/…`, файлы в `_media/images/…`.
- Внутренние `index.php?option=com_content…` уже заменены на SEF-адреса.
- Встречаются шорткоды Joomla и iframe Яндекс.Форм — вычистить при импорте.
- Материалы id 40 «Контакты:» и id 41 «О нас» без адреса — старые контакты ПрофиТруда, **не использовать**.

## 4. Стек и решения

- **Python 3.12+, Django 5.2 LTS**, PostgreSQL 16 (обязателен и локально: поиск на tsvector; удобнее всего `docker compose up`).
- Зависимости — **Poetry** (`pyproject.toml`, версии зафиксированы в lock).
- Конфигурация — **django-environ**, `.env` (в `.gitignore`), шаблон `.env.example`. Секреты не коммитить.
- Редактирование контента — **Django admin** + CKEditor 5 (`django-ckeditor-5`). Весь HTML из админки и импорта
  проходит санитайзер **nh3** (белый список тегов/атрибутов) при сохранении.
- Фронт — шаблоны Django, общий CSS на токенах (раздел 7), минимум JS (ванильный или Alpine.js). Без SPA.
- Статика — WhiteNoise; медиа — локально (`MEDIA_ROOT`), с возможностью перейти на S3/MinIO через django-storages.
- Поиск — PostgreSQL full-text (`SearchVector` с конфигурацией `russian`).
- Деплой — как у proverka.by: Ubuntu + Gunicorn (systemd) за Nginx на CWP. Плюс `Dockerfile` и `docker-compose.yml` для разработки и тестов.
- «Онлайн-сервис учёта по ОТ» на главной — пока **блок-описание со ссылкой-заглушкой** `[URL СЕРВИСА]`. Кабинет не делаем.

## 5. Архитектура

```
config/            settings (base/dev/prod/test), urls, wsgi, asgi
apps/core/         SiteSettings (синглтон: телефоны, почта, реквизиты, ссылки соцсетей), контекст-процессор,
                   базовые шаблоны, шапка/подвал как include, главная
apps/content/      Category, Material, представления разделов и материалов, поиск, карта сайта (HTML)
apps/leads/        Lead, формы заявок, уведомления
apps/seo/          Redirect, Gone, middleware 301/410, sitemap.xml, robots.txt, canonical
templates/         base.html, includes/header.html, includes/footer.html, content/*.html, …
static/css/        tokens.css, base.css, components.css
```

### Модели (минимум, уточнять по ходу)

`Category` — раздел: `title`, `slug` (уникальный), `parent` (FK self), `kind` (вопрос-ответ / инструкции / приказы /
карты рисков / статьи / документы / услуги ОТ / услуги СУОТ), `description`, `legacy_id`, `ordering`, SEO-поля,
`is_published`. Адрес: `/<slug>/`.

`Material` — единая модель для всех страниц-материалов:
- `type` (TextChoices): `service`, `article`, `document`, `instruction`, `order_sample`, `risk_card`, `faq`,
  `requirement` (справки «Охрана труда при…»), `page`;
- `title`, `slug` (**уникальный глобально** — адреса плоские), `category` (FK, null), `intro` (HTML), `body` (HTML),
  `short_answer` (блок «Коротко» у вопросов), `price_from` (Decimal, null), `price_unit`, `file` (FileField,
  для образцов .docx/.pdf), `cover` (ImageField), `npa_checked_at` (Date, null), `related` (M2M self);
- `legacy_id`, `legacy_url` (как в выгрузке, для сверки), `hits`, `rating_avg`, `rating_votes`;
- `meta_title`, `meta_description`, `is_published`, `published_at`, `updated_at`;
- индекс по `slug`, `(type, is_published)`, `search_vector` (GIN).

`Lead` — заявка: `name`, `phone`, `email`, `organization`, `service` (строка), `headcount` (choices), `comment`,
`attachment` (файл), `source_url`, `consent` (bool, обязательное), `created_at`, `ip`, `user_agent`, `status`.

`Redirect` (`old_path` уникальный, `new_path`, `code` 301/302) и `Gone` (`path`) — заполняются из `redirects.csv`.

Логику держать в сервисных функциях (`services.py`), модели — тонкие.

### Адреса — главное требование

Старые адреса плоские. Новый сайт обязан отвечать **ровно по ним**:

| Шаблон | Что | Пример |
|---|---|---|
| `/` | главная | |
| `/<slug>.html` | материал (любой тип) | `/razrabotka-i-vnedrenie-suot-pod-klyuch.html` |
| `/<slug>/` | раздел | `/prikazy-po-ohrane-truda/`, `/chasto-zadavaemye-voprosy-po-ohrane-truda/` |
| `/pages/more-pages/vse-uslugi-po-suot.html` | хаб услуг СУОТ (вложенный путь Joomla — сохранить) | |

- Все строки `redirects.csv` с `action=keep` после импорта должны отдавать **200** — это главный тест (раздел 9).
- `action=301` → `Redirect`, `action=410` → `Gone`.
- Правила с `*` (хост http→https и www→без www, `/en/*`, `*/page-N.html`, битое тире в slug, utm-параметры →
  canonical) реализовать в middleware/Nginx, а не построчно.
- Slug с опечаткой `…kotlovkotlov.html` — **не исправлять**.
- Настоящая 404 с кодом 404 (не «мягкая» `/__404__.html`).

## 6. Страницы и макеты

| Макет | Страница | Источник данных |
|---|---|---|
| `Shapka`, `Podval` | общие include шапки и подвала | `SiteSettings`, меню в шаблоне |
| `Main` | главная `/` | статичные блоки + выборки (услуги, популярные вопросы) |
| `Uslugi` | хаб услуг `/uslugi-po-ohrane-truda-v-minske-i-po-belarusi.html` | `Material(type=service)` двумя группами |
| `Usluga` | шаблон услуги | `Material(type=service)`: текст, цена, «вопросы по теме», форма с подставленной услугой |
| `Ceny` | `/ceny-na-razrabotku-suot-v-minske.html` (+301 со `/stoimost-razrabotki-i-vnedreniya-suot.html` — согласовать с пользователем) | `price_from` услуг |
| `Razdel` | шаблон раздела `/<slug>/` | `Category` + список, поиск в разделе, сортировка, пагинация |
| `Dokument` | образцы приказов, инструкции, карты рисков, «Нужные документы» | `Material`: тело как «лист», файл для скачивания, «НПА проверены» |
| `Statya` | статьи | узкая колонка, оглавление по `h2`, врезка с услугой |
| `VoprosOtvet` | хаб `/chasto-zadavaemye-voprosy-po-ohrane-truda/` | 13 подразделов со счётчиками, топ по `hits`, поиск |
| `Vopros` | вопросы и справки «Охрана труда при…» | `short_answer` + ответ + «Основание» + связанные |
| `ONas` | `/o-nas.html` | статичная + список клиентов |
| `Klienty` | `/nashi-klienty.html` | список организаций (из материала id 39) |
| `Kontakty` | `/kontakty.html` | `SiteSettings` + форма `Lead` |
| `Usloviya` | `/usloviya-okazaniya-uslug.html` + политика ПДн + cookie | статичная (текст политики — от пользователя) |
| `KartaSajta` | `/karta-sajta.html` | дерево разделов и материалов |
| `Oshibka404` | шаблон 404 | |

Тексты в квадратных скобках в макетах (`[ЦЕНА]`, `[СРОК]`, `[Имя Фамилия]`, отзывы, адрес, часы работы) — **заглушки**,
не выдумывать значения: вынести в `SiteSettings`/админку и оставить пустыми.

## 7. Дизайн-токены (из макетов)

```css
--font: 'Onest', system-ui, sans-serif;   /* Google Fonts, веса 400–800 */
--bg: #F6F4EF;  --surface: #FFFFFF;  --surface-2: #FBFAF7;
--ink: #14212B; --text: #2A3843; --text-2: #3C4A55; --muted: #5E6872;
--border: #DDD9CE; --border-2: #E6E2D8; --border-dashed: #B9B4A6;
--accent: #C2410C;  --accent-ink: #8A2F08; --accent-soft: #FBE3D4; --accent-bg: #FFF8F3; --accent-line: #F3C7AE;
--dark: #14212B; --dark-2: #1E3140; --dark-text: #C6D1DA; --dark-accent: #F4A77E;
--info-bg: #EAF1F6; --info-ink: #1A4F78;
--viber: #7360F2; --telegram: #1F7FB8;
/* контейнер max-width 1200px, поля 24px; радиусы 10/12/16/18/20px; секции padding 56–80px */
```

Адаптив: всё на `flex-wrap`/`grid auto-fill`, на телефоне колонки складываются; цели нажатия ≥44px; контраст ≥4.5:1.

## 8. Импорт (management-команды)

1. `import_joomla --source data/content` — идемпотентно (upsert по `legacy_id`):
   разделы из `_index.md` → `Category`; материалы → `Material` (тип по полю `type`); Markdown → HTML
   (`markdown` + таблицы), затем **nh3**; `<!-- readmore -->` делит `intro`/`body`; картинки из `_media/` → `MEDIA_ROOT`
   с переписыванием путей; slug берётся из `url` без `.html`; `hits`, рейтинг, даты, meta переносятся.
   Пропускать `_korzina/`, `stranicy-shablona/`, `sluzhebnye/`, демо-материалы.
   В конце — отчёт: сколько создано/обновлено/пропущено, битые ссылки и картинки.
2. `import_redirects --csv docs/data/redirects.csv` — заполняет `Redirect`/`Gone`, сообщает о правилах с `*`.
3. `check_legacy_urls` — проходит по всем `keep` и проверяет 200 через тестовый клиент; ненулевой код выхода при ошибках.

## 9. Качество, безопасность, тесты

- PEP 8: **ruff** (lint + isort), **black**; **mypy** + django-stubs; **radon** для сложности. Всё — в **pre-commit**.
- **pytest + pytest-django**, покрытие **>80%** (`pytest-cov`), factory-boy для фикстур.
  Обязательные тесты: модели и сервисы; санитайзер (XSS-векторы); импорт на 5–10 образцах (`tests/fixtures/export/`);
  все `keep`-адреса → 200; 301/410 из CSV; формы (CSRF, honeypot, лимит частоты, типы и размер файлов, согласие ПДн);
  sitemap/robots; 404 отдаёт код 404; миграции вперёд и назад.
- **Bandit** и `pip-audit` в CI. Нагрузочный сценарий **locust** (`loadtests/`) для главной, раздела, материала, поиска.
- Безопасность: CSRF везде, ORM без сырого SQL, `SECURE_*`, HSTS, CSP (django-csp), `X-Frame-Options`,
  загрузки — белый список (pdf, doc, docx, xls, xlsx, jpg, png), лимит размера, хранение вне webroot, случайные имена;
  админка на неочевидном пути + 2FA (django-otp) — согласовать; rate limit форм (django-ratelimit).
- Логирование: отдельный логгер `security` (заявки, ошибки форм, 410/404-всплески), Sentry по `SENTRY_DSN`.
- Уведомления о заявке — e-mail (SMTP из `.env`), опционально Telegram-бот.
- CI: **GitHub Actions** — lint, mypy, tests с Postgres-сервисом, bandit, сборка Docker-образа.

## 10. Правила кода (от пользователя — обязательно)

- Подробные комментарии **на русском**, объясняющие нетривиальную логику.
- **В начале каждого файла — комментарий с полным путём файла** (например `# apps/content/models.py`).
- Эмодзи в комментариях для наглядности: ⚠️ опасное место, 💡 идея, ✅ проверено, 🔐 безопасность.
- При правке существующего кода — помечать, что изменено (`# ✏️ ИЗМЕНЕНО: …`).
- Docstring у функций и классов: аргументы, типы, что возвращает. Аннотации типов везде.
- Class-based views; `select_related`/`prefetch_related`; кэш (Redis при наличии, иначе locmem) для главной и разделов.
- Миграции — маленькие и по смыслу, проверять откат.
- Коммиты — **Conventional Commits** (`feat:`, `fix:`, `chore:`…), ветки `feature/*`, PR в `main`.
- Перед реализацией крупного шага — коротко план в чате и ожидание подтверждения пользователя.
- В конце каждого ответа — рекомендации по улучшению.

## 11. Порядок работ

1. Каркас: Poetry, settings, приложения, pre-commit, Docker, CI, `.env.example`, README.
2. Модели, админка, миграции, санитайзер.
3. Импорт (сначала на образцах в `tests/fixtures/export/`, потом на полной выгрузке) + `check_legacy_urls`.
4. Шаблоны и CSS по макетам: base → шапка/подвал → главная → материал (все типы) → разделы → хабы → служебные.
5. Формы заявок, уведомления.
6. SEO: redirects/410, sitemap.xml, robots.txt, canonical, Open Graph, schema.org (Organization, FAQPage для вопросов,
   Service для услуг, BreadcrumbList).
7. Тесты, locust, bandit; деплой на staging (systemd unit, nginx-конфиг, инструкция в `docs/deploy.md`).

## 12. Открытые вопросы к пользователю

- Данные с Диска (выгрузка `content/`, `old_site.sqlite`, `_media/`) — как передать.
- Склеивать ли две страницы цен (`/ceny-…` и `/stoimost-…`) — по трафику.
- Текст политики обработки ПДн (на старом сайте нет — нужен до запуска форм).
- Актуальность e-mail 3570911@tut.by; адрес для корреспонденции; часы работы.
- Цены и сроки для тарифов (в макетах заглушки).
- Ссылка на онлайн-сервис учёта по ОТ, если он уже существует.
- Оставлять ли поиск по сайту отдельной страницей (`/search.html` на старом сайте давал ~22 800 обращений).

## 13. Что проверить в контенте (не править молча — сообщать)

- В образцах и вопросах встречаются устаревшие НПА: ТКП 181-2009 (действует ТКП 181-2023), СТБ 18001-2009
  (заменён СТБ ISO 45001-2020), пост. № 70 (МОПОТ), Инструкция № 175 — сверять с действующими редакциями;
  в `redirects.csv` такие страницы помечены «проверить актуальность ссылок на НПА», в выгрузке — `audit_flags`.
- 127 ссылок на ohranatruda.of.by, 8 — на attestation.by, 6 — на ohrana-truda.by — партнёрские, сохранить.
