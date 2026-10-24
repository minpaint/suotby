# apps/leads/templatetags/leads_tags.py — вывод формы заявки в любом шаблоне
from __future__ import annotations

from typing import Any

from django import template

from apps.leads.forms import SERVICE_CHOICES, LeadForm

register = template.Library()


@register.inclusion_tag("leads/_form.html", takes_context=True)
def lead_form(
    context: dict[str, Any],
    variant: str = "full",
    service: str = "",
    title: str = "",
    button: str = "Отправить заявку",
) -> dict[str, Any]:
    """
    Форма заявки.

    Args:
        context: контекст шаблона (нужен request для CSRF и адреса страницы).
        variant: ``full`` — все поля (контакты), ``short`` — имя, телефон, численность (главная, услуга).
        service: предзаполненная услуга (на странице услуги — её название).
        title: заголовок над формой.
        button: текст кнопки.

    Returns:
        Контекст шаблона ``leads/_form.html``.
    """
    request = context.get("request")
    form = LeadForm(initial={"service": service, "source_url": request.path if request else ""})
    return {
        "form": form,
        "variant": variant,
        "service": service,
        "service_choices": SERVICE_CHOICES,
        "title": title,
        "button": button,
        "request": request,
        "csrf_token": context.get("csrf_token"),
    }
