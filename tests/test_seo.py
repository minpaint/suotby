# tests/test_seo.py — старые адреса, 301/410, sitemap, robots
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

from apps.content.importer import JoomlaImporter
from apps.seo.legacy_csv import read_rows
from apps.seo.models import Gone, Redirect
from apps.seo.services import pattern_redirect

pytestmark = pytest.mark.django_db
CSV = Path(__file__).resolve().parent.parent / "docs" / "data" / "redirects.csv"


@pytest.fixture
def redirects(seeded: None) -> None:
    call_command("import_redirects", csv=str(CSV))


def test_csv_loaded(redirects: None) -> None:
    assert Redirect.objects.count() > 40
    assert Gone.objects.filter(path="/log-in.html").exists()
    assert not Redirect.objects.filter(old_path__contains="*").exists()


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("/about.html", "/o-nas.html"),
        ("/search.html", "/"),
        ("/table/stati/", "/stati/"),
        ("/en/o-nas.html", "/o-nas.html"),
        ("/en/about.html", "/o-nas.html"),  # цепочка сведена в один шаг
        ("/stati/page-2.html", "/stati/"),
        ("/index.php", "/"),
        (
            "/razrabotka-sistemy-upravleniya-ohranoj-truda-%E2%80%93-eto-obyazatelno.html",
            "/razrabotka-sistemy-upravleniya-ohranoj-truda-eto-obyazatelno.html",
        ),
    ],
)
def test_301(redirects: None, client: Client, old: str, new: str) -> None:
    resp = client.get(old)
    assert resp.status_code == 301
    assert resp.headers["Location"] == new


def test_301_keeps_query(redirects: None, client: Client) -> None:
    assert client.get("/about.html?utm_source=x").headers["Location"] == "/o-nas.html?utm_source=x"


def test_410(redirects: None, client: Client) -> None:
    resp = client.get("/log-in.html")
    assert resp.status_code == 410
    assert "удалена" in resp.content.decode()


def test_www_to_canonical_host(seeded: None) -> None:
    resp = Client(HTTP_HOST="www.suot.by").get("/o-nas.html?a=1")
    assert resp.status_code == 301
    assert resp.headers["Location"] == "https://suot.by/o-nas.html?a=1"


def test_admin_not_redirected(redirects: None, client: Client) -> None:
    Redirect.objects.create(old_path="/upravlenie/", new_path="/")
    assert client.get("/upravlenie/").status_code == 302  # на страницу входа, а не на главную


def test_redirect_cache_reset_on_change(redirects: None, client: Client) -> None:
    assert client.get("/new-old.html").status_code == 404
    Redirect.objects.create(old_path="/new-old.html", new_path="/o-nas.html", code=302)
    assert client.get("/new-old.html").status_code == 302


def test_pattern_rules() -> None:
    assert pattern_redirect("/en") == "/"
    assert pattern_redirect("/obychnyj.html") is None
    assert (
        pattern_redirect("/razrabotka-sistemy-upravleniya-ohranoj-truda-eto-obyazatelno.html")
        is None
    )


def test_keep_urls_from_fixtures_are_200(
    imported: JoomlaImporter, redirects: None, client: Client
) -> None:
    """Главный тест переезда на образцах: каждый keep-адрес, который есть в образцах выгрузки, открывается."""
    from apps.content.models import Category, Material

    paths = set(Material.objects.values_list("path", flat=True)) | set(
        Category.objects.exclude(path=None).values_list("path", flat=True)
    )
    keep = [r.old_path for r in read_rows(CSV) if r.action == "keep" and not r.is_pattern]
    covered = [p for p in keep if p in paths or p.replace("-–-", "-") in paths]
    assert len(covered) >= 20
    for p in covered:
        assert client.get(p).status_code == 200, p


def test_check_legacy_urls_command(
    imported: JoomlaImporter, redirects: None, tmp_path: Path
) -> None:
    csv = tmp_path / "r.csv"
    csv.write_text(
        "old_path;new_path;action;type;priority;traffic;note\n"
        "/o-nas.html;/o-nas.html;keep;о компании;;;\n"
        "/about.html;/o-nas.html;301;дубль;;;\n"
        "/log-in.html;;410;служебная;;;\n",
        encoding="utf-8",
    )
    call_command("check_legacy_urls", csv=str(csv))
    csv.write_text(
        "old_path;new_path;action;type;priority;traffic;note\n/net.html;/net.html;keep;x;;;\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        call_command("check_legacy_urls", csv=str(csv))


def test_robots_and_sitemap(imported: JoomlaImporter, client: Client) -> None:
    robots = client.get("/robots.txt").content.decode()
    assert "Sitemap: https://suot.by/sitemap.xml" in robots
    assert "upravlenie" not in robots
    sitemap = client.get("/sitemap.xml").content.decode()
    assert "/obsluzhivanie-organizacii-v-kachestve-specialista-po-ohrane-truda.html" in sitemap
    assert "/organizaciya-raboty-po-ohrane-truda/" in sitemap
    assert "https://" in sitemap
