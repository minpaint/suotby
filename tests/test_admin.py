# tests/test_admin.py — админка открывается и работает
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.content.importer import JoomlaImporter
from apps.content.models import Material
from apps.core.models import SiteSettings

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(imported: JoomlaImporter) -> Client:
    c = Client(HTTP_HOST="suot.by")
    c.force_login(get_user_model().objects.create_superuser("admin", "a@a.by", "pass-12345-long"))
    return c


@pytest.mark.parametrize(
    "url",
    [
        "/upravlenie/",
        "/upravlenie/content/material/",
        "/upravlenie/content/category/",
        "/upravlenie/content/priceitem/",
        "/upravlenie/leads/lead/",
        "/upravlenie/seo/redirect/",
        "/upravlenie/core/client/",
        "/upravlenie/core/testimonial/",
        "/upravlenie/core/teammember/",
        "/upravlenie/seo/gone/",
    ],
)
def test_admin_lists(admin_client: Client, url: str) -> None:
    assert admin_client.get(url).status_code == 200


def test_material_change_page(admin_client: Client) -> None:
    m = Material.objects.get(legacy_id="71")
    resp = admin_client.get(f"/upravlenie/content/material/{m.pk}/change/")
    assert resp.status_code == 200
    assert m.path in resp.content.decode()


def test_settings_singleton_redirect(admin_client: Client) -> None:
    resp = admin_client.get("/upravlenie/core/sitesettings/")
    assert resp.status_code == 302
    assert admin_client.get(resp.headers["Location"]).status_code == 200
    s = SiteSettings.load()
    assert admin_client.get(f"/upravlenie/core/sitesettings/{s.pk}/delete/").status_code == 403


def test_admin_actions(admin_client: Client) -> None:
    ids = [str(m.pk) for m in Material.objects.filter(legacy_id__in=["71", "75"])]
    for action in ("mark_npa_checked", "unpublish", "publish"):
        admin_client.post(
            "/upravlenie/content/material/", {"action": action, "_selected_action": ids}
        )
    assert (
        Material.objects.filter(pk__in=ids, npa_checked_at__isnull=False, is_published=True).count()
        == 2
    )


def test_material_save_via_admin(admin_client: Client) -> None:
    m = Material.objects.get(legacy_id="75")
    old = m.updated_at
    from django.contrib.admin.sites import site

    from apps.content.admin import MaterialAdmin

    ma = MaterialAdmin(Material, site)
    request = type("R", (), {"user": None})()
    ma.save_model(request, m, None, True)
    m.refresh_from_db()
    assert m.updated_at >= old
