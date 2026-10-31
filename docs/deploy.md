# Развёртывание suot.by

Схема как у proverka.by: **Ubuntu + PostgreSQL + Gunicorn (systemd) за Nginx на CWP**.

## 1. Локальная разработка

```bash
git clone https://github.com/minpaint/suotby.git && cd suotby
docker compose up            # PostgreSQL + сайт на http://localhost:8000
docker compose run --rm tests  # тесты в отдельном контейнере
```

Без Docker:

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install poetry==2.1.3 && poetry install --no-root
cp .env.example .env         # DEBUG=True, DJANGO_SETTINGS_MODULE=config.settings.dev, DATABASE_URL=…
python manage.py migrate
python manage.py seed_site
python manage.py import_redirects
python manage.py import_joomla --source data/content   # выгрузка с Google Диска
python manage.py createsuperuser
python manage.py runserver
pre-commit install
```

## 2. Staging и прод (сервер)

### 2.1. Пользователь, папки, база

```bash
sudo adduser --system --group --home /srv/suotby suotby
sudo mkdir -p /srv/suotby/{media,private_media} /var/log/suotby
sudo chown -R suotby:suotby /srv/suotby /var/log/suotby
sudo -u postgres psql -c "CREATE USER suot WITH PASSWORD '…';" -c "CREATE DATABASE suot OWNER suot;"
```

### 2.2. Код и зависимости

```bash
sudo -u suotby git clone https://github.com/minpaint/suotby.git /srv/suotby/app
sudo -u suotby python3.12 -m venv /srv/suotby/venv
sudo -u suotby /srv/suotby/venv/bin/pip install poetry==2.1.3
cd /srv/suotby/app && sudo -u suotby /srv/suotby/venv/bin/poetry install --no-root --only main
sudo -u suotby cp .env.example .env && sudo -u suotby nano .env   # SECRET_KEY, DATABASE_URL, почта…
sudo chmod 600 /srv/suotby/app/.env
```

### 2.3. Первичное наполнение

```bash
cd /srv/suotby/app
export $(grep -v '^#' .env | xargs)
/srv/suotby/venv/bin/python manage.py migrate
/srv/suotby/venv/bin/python manage.py collectstatic --noinput
/srv/suotby/venv/bin/python manage.py import_joomla --source /srv/suotby/import/content --report /srv/suotby/import/report.txt
/srv/suotby/venv/bin/python manage.py import_redirects
/srv/suotby/venv/bin/python manage.py check_legacy_urls      # ✅ должно быть «ошибок: 0»
/srv/suotby/venv/bin/python manage.py createsuperuser
```

### 2.4. Gunicorn и Nginx

```bash
sudo cp deploy/suotby.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now suotby
# Nginx: содержимое deploy/nginx-suot.by.conf — в vhost suot.by в CWP (сертификаты оставить текущие)
sudo nginx -t && sudo systemctl reload nginx
```

### 2.5. Обновление

```bash
cd /srv/suotby/app && sudo -u suotby git pull
sudo -u suotby /srv/suotby/venv/bin/poetry install --no-root --only main
sudo -u suotby /srv/suotby/venv/bin/python manage.py migrate
sudo -u suotby /srv/suotby/venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart suotby
```

## 3. Переключение со старого сайта (чек-лист)

1. Staging на поддомене (например `new.suot.by`), закрыт от индексации (`X-Robots-Tag: noindex` в Nginx).
2. Импорт выгрузки, `check_legacy_urls` — **0 ошибок**.
3. Вычитка: цены, политика ПДн, контакты, тексты услуг (раздел 12 CLAUDE.md).
4. Тест формы заявки: письмо и (если включено) Telegram доходят.
5. Резервная копия Joomla (файлы + БД) — хранить минимум 3 месяца.
6. Переключение vhost suot.by на новый конфиг Nginx.
7. Сразу после: `check_legacy_urls` на проде, Яндекс.Вебмастер и Google Search Console — отправить `sitemap.xml`,
   смотреть ошибки обхода 2–4 недели.

## 4. Мониторинг

- Ошибки — Sentry (`SENTRY_DSN` в `.env`).
- Журналы: `/var/log/suotby/app.log`, `security.log` (заявки, отказы форм, лимиты), `access.log`.
- Метрики (по желанию): `django-prometheus` + Grafana.

## 5. Резервные копии

```bash
# cron, ежедневно 03:00
pg_dump -Fc suot > /backup/suot-$(date +%F).dump
tar czf /backup/suot-media-$(date +%F).tgz /srv/suotby/media /srv/suotby/private_media
```
