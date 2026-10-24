# suot.by — сайт на Django

Новая версия сайта [suot.by](https://suot.by/) (разработка СУОТ и услуги по охране труда в Минске и по Беларуси):
перенос с Joomla 4 на Python/Django по готовым макетам с сохранением всех старых адресов.

## Быстрый старт

```bash
docker compose up                      # PostgreSQL + сайт: http://localhost:8000
docker compose run --rm tests          # тесты
```

Админка: `/upravlenie/` (адрес задаётся `ADMIN_URL`). Пользователь — `python manage.py createsuperuser`.

## Команды

| Команда | Что делает |
|---|---|
| `seed_site` | разделы, служебные страницы, клиенты, позиции цен (повторный запуск безопасен) |
| `import_joomla --source data/content` | импорт выгрузки старого сайта (тексты, картинки), идемпотентно |
| `import_redirects` | 301 и 410 из `docs/data/redirects.csv` |
| `check_legacy_urls` | проверка всех старых адресов: keep → 200, 301, 410 (код выхода 1 при ошибках) |

## Устройство

```
config/          настройки base/dev/test/prod, маршруты
apps/core/       настройки сайта (контакты, реквизиты, политика ПДн), главная, клиенты, отзывы, команда, санитайзер HTML
apps/content/    разделы, материалы (услуги, статьи, образцы, вопросы), цены, импорт Joomla, поиск
apps/leads/      заявки: форма, защита от спама, уведомления (почта, Telegram), закрытые вложения
apps/seo/        переадресации и 410, sitemap.xml, robots.txt
templates/       шаблоны по макетам docs/mockups
static/css/      токены и стили из макетов
deploy/          systemd-юнит и конфиг Nginx
tests/           pytest (покрытие > 80%), образцы выгрузки в tests/fixtures/export
loadtests/       нагрузочный сценарий locust
```

## Документы

- ТЗ и правила работы — [`CLAUDE.md`](CLAUDE.md)
- Развёртывание и переключение со старого сайта — [`docs/deploy.md`](docs/deploy.md)
- Макеты — [`docs/mockups/`](docs/mockups/), карта старого сайта — [`docs/data/`](docs/data/)
