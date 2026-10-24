# apps/leads/views.py — приём заявок и выдача вложений сотрудникам
from __future__ import annotations

import logging
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import TemplateView
from django_ratelimit.decorators import ratelimit

from apps.leads.forms import LeadForm
from apps.leads.models import Lead
from apps.leads.services import create_lead

security_log = logging.getLogger("security")


@method_decorator(
    ratelimit(key="ip", rate=settings.LEAD_RATE, method="POST", block=False), name="post"
)
class LeadCreateView(View):
    """POST /zayavka/ — принимает заявку с любой формы сайта."""

    def get(self, request: HttpRequest) -> HttpResponse:
        return HttpResponseRedirect("/kontakty.html")

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Сохраняет заявку или показывает форму с ошибками на отдельной странице.

        🔐 Превышение лимита и honeypot не раскрываются боту: ответ выглядит как успех.
        """
        form = LeadForm(request.POST, request.FILES)
        if getattr(request, "limited", False):
            security_log.warning("Лимит заявок превышен: %s", request.META.get("REMOTE_ADDR"))
            return render(request, "leads/error.html", {"limited": True}, status=429)
        if form.is_spam:
            security_log.warning("Honeypot сработал: %s", request.META.get("REMOTE_ADDR"))
            return HttpResponseRedirect("/zayavka/spasibo/")
        if not form.is_valid():
            security_log.info("Заявка не прошла проверку: %s", list(form.errors))
            return render(
                request, "leads/error.html", {"form": form, "back": self._back(request)}, status=400
            )
        create_lead(form, request)
        messages.success(request, "Заявка отправлена")
        return HttpResponseRedirect("/zayavka/spasibo/")

    @staticmethod
    def _back(request: HttpRequest) -> str:
        """Безопасная ссылка «вернуться» (только на свой сайт)."""
        ref = request.POST.get("source_url") or request.META.get("HTTP_REFERER", "")
        if url_has_allowed_host_and_scheme(ref, allowed_hosts={request.get_host()}):
            return ref
        return "/kontakty.html"


class LeadThanksView(TemplateView):
    """Страница «Спасибо, заявка отправлена»."""

    template_name = "leads/thanks.html"


@staff_member_required
def lead_attachment(request: HttpRequest, pk: int) -> FileResponse:
    """
    🔐 Отдаёт вложение заявки только сотрудникам.

    Args:
        request: запрос сотрудника.
        pk: id заявки.

    Raises:
        Http404: если файла нет.
    """
    lead = get_object_or_404(Lead, pk=pk)
    if not lead.attachment:
        raise Http404
    try:
        fh = lead.attachment.open("rb")
    except FileNotFoundError as exc:
        raise Http404 from exc
    name = Path(lead.attachment.name or "file").name
    security_log.info("Скачано вложение заявки #%s пользователем %s", pk, request.user)
    return FileResponse(fh, as_attachment=True, filename=name)
