# apps/leads/services.py — сохранение заявки и уведомления
from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpRequest

from apps.leads.forms import LeadForm
from apps.leads.models import Lead

logger = logging.getLogger("apps.leads")
security_log = logging.getLogger("security")


def client_ip(request: HttpRequest) -> str | None:
    """
    IP посетителя. За Nginx берётся первый адрес из X-Forwarded-For.

    ⚠️ Доверять X-Forwarded-For можно только если сайт доступен исключительно через свой Nginx.
    """
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip = forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")
    return ip or None


def create_lead(form: LeadForm, request: HttpRequest) -> Lead:
    """
    Сохраняет заявку из валидной формы и рассылает уведомления.

    Args:
        form: провалидированная форма.
        request: запрос (для IP, браузера и страницы-источника).

    Returns:
        Сохранённая заявка.
    """
    lead: Lead = form.save(commit=False)
    lead.ip = client_ip(request)
    lead.user_agent = request.META.get("HTTP_USER_AGENT", "")[:300]
    lead.source_url = (form.cleaned_data.get("source_url") or request.META.get("HTTP_REFERER", ""))[
        :500
    ]
    if lead.attachment:
        lead.attachment_name = (lead.attachment.name or "")[-255:]
    lead.save()
    security_log.info("Заявка #%s с %s, страница %s", lead.pk, lead.ip, lead.source_url)
    notify(lead)
    return lead


def lead_text(lead: Lead) -> str:
    """Текст уведомления о заявке."""
    lines = [
        f"Новая заявка #{lead.pk} с сайта",
        f"Имя: {lead.name}",
        f"Телефон: {lead.phone}",
        f"E-mail: {lead.email or '—'}",
        f"Организация: {lead.organization or '—'}",
        f"Что нужно: {lead.service or '—'}",
        f"Численность: {lead.get_headcount_display() or '—'}",
        f"Комментарий: {lead.comment or '—'}",
        f"Файл: {'есть (см. админку)' if lead.attachment else 'нет'}",
        f"Страница: {lead.source_url or '—'}",
    ]
    return "\n".join(lines)


def notify(lead: Lead) -> None:
    """
    Отправляет уведомление на почту и (если настроен) в Telegram.

    💡 Ошибка отправки не должна терять заявку: она уже в базе, сбой только пишется в журнал.
    """
    text = lead_text(lead)
    if settings.LEADS_NOTIFY_EMAILS:
        try:
            send_mail(f"Заявка с suot.by: {lead.name}", text, None, settings.LEADS_NOTIFY_EMAILS)
        except Exception:  # pragma: no cover — сетевые сбои SMTP
            logger.exception("Не удалось отправить письмо о заявке #%s", lead.pk)
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
        send_telegram(text)


def send_telegram(text: str) -> bool:
    """
    Отправляет сообщение в Telegram через Bot API.

    Args:
        text: текст сообщения.

    Returns:
        True, если Telegram ответил успехом.
    """
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload: dict[str, Any] = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    try:
        # 🔐 адрес фиксированный (https://api.telegram.org), пользовательский ввод в него не попадает
        resp = urllib.request.urlopen(req, timeout=5)  # noqa: S310  # nosec B310
        with resp:
            return bool(resp.status == 200)
    except Exception:  # pragma: no cover
        logger.exception("Не удалось отправить заявку в Telegram")
        return False
