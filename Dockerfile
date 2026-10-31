# Dockerfile — образ сайта для разработки, тестов и (при желании) прода
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.1.3 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install "poetry==${POETRY_VERSION}"
COPY pyproject.toml poetry.lock* ./
# --only main в проде; для тестов собирается с аргументом DEV=1
ARG DEV=0
RUN if [ "$DEV" = "1" ]; then poetry install --no-root --no-interaction; \
    else poetry install --no-root --only main --no-interaction; fi

COPY . .

# 🔐 приложение работает не от root
RUN useradd --create-home --uid 1000 app && mkdir -p /app/staticfiles /app/media /app/private_media \
    && chown -R app:app /app
USER app

RUN DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
