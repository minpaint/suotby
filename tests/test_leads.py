# tests/test_leads.py — заявки: валидация, защита, уведомления, вложения
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings

from apps.leads.models import Lead
from apps.leads.services import client_ip, lead_text

pytestmark = pytest.mark.django_db

VALID = {
    "name": "Иван",
    "phone": "+375 29 123-45-67",
    "consent": "on",
    "service": "Аудит",
    "source_url": "/kontakty.html",
}


def post(client: Client, data: dict, **extra) -> object:
    return client.post("/zayavka/", data, **extra)


def test_lead_created_and_notified(seeded: None, client: Client) -> None:
    resp = post(client, VALID, REMOTE_ADDR="10.0.0.1")
    assert resp.status_code == 302 and resp.headers["Location"] == "/zayavka/spasibo/"
    lead = Lead.objects.get()
    assert lead.ip == "10.0.0.1" and lead.source_url == "/kontakty.html"
    assert len(mail.outbox) == 1
    assert "+375 29 123-45-67" in mail.outbox[0].body


def test_consent_required(seeded: None, client: Client) -> None:
    data = {**VALID}
    data.pop("consent")
    resp = post(client, data)
    assert resp.status_code == 400
    assert "согласия" in resp.content.decode()
    assert not Lead.objects.exists()


@pytest.mark.parametrize("phone", ["abc", "12", "<script>"])
def test_bad_phone(seeded: None, client: Client, phone: str) -> None:
    assert post(client, {**VALID, "phone": phone}).status_code == 400


def test_name_with_link_rejected(seeded: None, client: Client) -> None:
    assert post(client, {**VALID, "name": "http://spam"}).status_code == 400


def test_honeypot_silently_dropped(seeded: None, client: Client) -> None:
    resp = post(client, {**VALID, "website": "http://bot"})
    assert resp.status_code == 302
    assert not Lead.objects.exists()


def test_csrf_enforced(seeded: None) -> None:
    c = Client(enforce_csrf_checks=True, HTTP_HOST="suot.by")
    assert c.post("/zayavka/", VALID).status_code == 403


@override_settings(LEAD_RATE="2/h")
def test_rate_limit(seeded: None, client: Client) -> None:
    # ⚠️ декоратор читает лимит при импорте, поэтому проверяем по факту: 6-я заявка подряд блокируется
    statuses = [post(client, VALID, REMOTE_ADDR="10.9.9.9").status_code for _ in range(6)]
    assert statuses[-1] == 429
    assert Lead.objects.count() == 5


def test_valid_pdf_attachment_saved_privately(seeded: None, client: Client) -> None:
    f = SimpleUploadedFile("штатное.pdf", b"%PDF-1.4 test", content_type="application/pdf")
    assert post(client, {**VALID, "attachment": f}).status_code == 302
    lead = Lead.objects.get()
    assert lead.attachment.name.startswith("leads/") and lead.attachment.name.endswith(".pdf")
    assert "штатное" not in lead.attachment.name  # имя случайное


@pytest.mark.parametrize(
    ("name", "content"),
    [("virus.exe", b"MZ"), ("fake.pdf", b"MZ\x90\x00"), ("doc.docx", b"not zip")],
)
def test_bad_attachment_rejected(seeded: None, client: Client, name: str, content: bytes) -> None:
    f = SimpleUploadedFile(name, content)
    assert post(client, {**VALID, "attachment": f}).status_code == 400


@override_settings(LEAD_ATTACHMENT_MAX_SIZE=10)
def test_attachment_too_big(seeded: None, client: Client) -> None:
    f = SimpleUploadedFile("a.pdf", b"%PDF-" + b"0" * 100)
    assert post(client, {**VALID, "attachment": f}).status_code == 400


def test_attachment_only_for_staff(seeded: None, client: Client) -> None:
    f = SimpleUploadedFile("a.pdf", b"%PDF-1.4")
    post(client, {**VALID, "attachment": f})
    lead = Lead.objects.get()
    url = f"/upravlenie/leads/file/{lead.pk}/"
    assert client.get(url).status_code == 302  # не сотрудник → на вход
    admin = get_user_model().objects.create_superuser("admin", "a@a.by", "pass-12345-long")
    client.force_login(admin)
    resp = client.get(url)
    assert resp.status_code == 200
    assert b"%PDF" in b"".join(resp.streaming_content)


def test_attachment_404_without_file(seeded: None, client: Client) -> None:
    post(client, VALID)
    admin = get_user_model().objects.create_superuser("admin", "a@a.by", "pass-12345-long")
    client.force_login(admin)
    assert client.get(f"/upravlenie/leads/file/{Lead.objects.get().pk}/").status_code == 404


def test_get_redirects_to_contacts(seeded: None, client: Client) -> None:
    assert client.get("/zayavka/").headers["Location"] == "/kontakty.html"


@override_settings(TELEGRAM_BOT_TOKEN="t", TELEGRAM_CHAT_ID="1")
def test_telegram_notification(seeded: None, client: Client) -> None:
    with mock.patch("apps.leads.services.send_telegram", return_value=True) as tg:
        post(client, VALID)
    tg.assert_called_once()


def test_send_telegram_request() -> None:
    from apps.leads import services

    fake = mock.MagicMock()
    fake.status = 200
    with (
        override_settings(TELEGRAM_BOT_TOKEN="t", TELEGRAM_CHAT_ID="1"),
        mock.patch("urllib.request.urlopen", return_value=fake) as op,
    ):
        assert services.send_telegram("hi") is True
    assert "api.telegram.org/bott/sendMessage" in op.call_args[0][0].full_url


def test_helpers(seeded: None) -> None:
    req = mock.Mock(META={"HTTP_X_FORWARDED_FOR": "1.2.3.4, 10.0.0.1", "REMOTE_ADDR": "10.0.0.1"})
    assert client_ip(req) == "1.2.3.4"
    lead = Lead.objects.create(name="А", phone="+375291234567", consent=True)
    assert "Новая заявка" in lead_text(lead)
    assert "А, +375291234567" in str(lead)


def test_lead_form_rendered_on_pages(seeded: None, client: Client) -> None:
    html = client.get("/kontakty.html").content.decode()
    assert 'name="csrfmiddlewaretoken"' in html
    assert 'name="website"' in html  # honeypot
    assert 'name="attachment"' in html
