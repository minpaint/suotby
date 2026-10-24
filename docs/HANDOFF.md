# Передача проекта в Claude Code

## 1. Подготовка на компьютере

```bash
git clone https://github.com/minpaint/suotby.git
cd suotby
mkdir data
```

Скопируй в `data/` с Google Диска (`coding/suot.by/`):

```
data/content/         ← вся папка content (md-файлы, _media, _manifest.*)
data/old_site.sqlite  ← из data/
data/audit/           ← из audit/ (pages.csv, npa.csv, links.csv)
```

Папка `data/` в git не попадает — это исходники для импорта.

## 2. Первый запрос в Claude Code

Открой Claude Code в папке `suotby` и вставь:

```
Прочитай CLAUDE.md, макеты в docs/mockups и данные в docs/data.
Данные выгрузки лежат в data/content, исходная БД — data/old_site.sqlite.

Начни с шага 1 «Каркас» из раздела 11: Poetry, settings на django-environ,
приложения core/content/leads/seo, pre-commit, Dockerfile + docker-compose, GitHub Actions,
.env.example, README. Сначала покажи план и структуру файлов, дождись моего «ок», потом пиши код.
Работай в ветке feature/skeleton.
```

Дальше — по одному шагу из раздела 11 `CLAUDE.md`, каждый в своей ветке с PR в `main`.

## 3. Что уже решено

- Django 5.2 LTS, PostgreSQL, Django admin + CKEditor 5, санитайзер nh3.
- Все старые адреса (`/slug.html`, `/razdel/`) сохраняются; 301/410 — из `docs/data/redirects.csv`.
- Деплой как у proverka.by: Gunicorn + Nginx на CWP; Docker — для разработки и тестов.
- Онлайн-сервис учёта по ОТ — пока только блок на главной.

## 4. Что ещё нужно от владельца

См. раздел 12 «Открытые вопросы» в `CLAUDE.md`.
