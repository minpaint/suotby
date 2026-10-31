# tests/test_pages.py — страницы сайта открываются и показывают нужное
import pytest
from django.test import Client

from apps.content.importer import JoomlaImporter
from apps.content.models import Material, PriceItem
from apps.core.models import TeamMember, Testimonial
from tests.factories import MaterialFactory

pytestmark = pytest.mark.django_db


def test_organization_legacy_alias(client: Client) -> None:
    """Два старых адреса показывают одну услугу с одним каноническим адресом."""
    primary = "/kachestvennaya-razrabotka-dokumentov-po-ohrane-truda-individualno-dlya-vashej-organizacii.html"
    alias = "/organizaciya-raboty-po-ohrane-truda-v-organizacii.html"
    material = MaterialFactory(path=primary, type=Material.Type.SERVICE, legacy_id="34")
    for path in (primary, alias):
        response = client.get(path)
        assert response.status_code == 200
        assert response.context["material"].pk == material.pk
        assert response.context["canonical_url"].endswith(primary)
        assert response.content.decode().count("<h1 ") == 1
    material.is_published = False
    material.save()
    assert client.get(alias).status_code == 404


@pytest.mark.parametrize(
    ("path", "text"),
    [
        ("/", "Разработка СУОТ и услуги по охране труда"),
        ("/uslugi-po-ohrane-truda-v-minske-i-po-belarusi.html", "Разработка СУОТ"),
        ("/pages/more-pages/vse-uslugi-po-suot.html", "Услуги по охране труда"),
        (
            "/obsluzhivanie-organizacii-v-kachestve-specialista-po-ohrane-truda.html",
            "Задать вопрос по услуге",
        ),
        ("/ceny-na-razrabotku-suot-v-minske.html", "От чего зависит цена"),
        ("/prikazy-po-ohrane-truda/", "Приказ о назначении ответственных"),
        (
            "/prikaz-o-naznachenii-otvetstvennyh-po-ohrane-truda-primernyj-obrazec.html",
            "Образец приказа",
        ),
        ("/obyazannosti-specialista-po-ohrane-truda-nakazanie-ili-blago.html", "В статье"),
        ("/chasto-zadavaemye-voprosy-po-ohrane-truda/", "Организация работы по охране труда"),
        ("/organizaciya-raboty-po-ohrane-truda/", "внеплановый инструктаж"),
        (
            "/v-kakih-sluchayah-i-v-kakom-poryadke-provoditsya-vneplanovyj-instruktazh-po-ohrane-truda.html",
            "FAQPage",
        ),
        ("/ohrana-truda-pri-vypolnenii-rabot-na-vysote.html", "Требования охраны труда"),
        (
            "/razrabotka-sistemy-upravleniya-ohranoj-truda-eto-obyazatelno.html",
            "Требование по разработке",
        ),
        ("/o-nas.html", "Нам доверяют"),
        ("/nashi-klienty.html", "ООО «Жибуль»"),
        ("/kontakty.html", "Заявка на расчёт"),
        ("/usloviya-okazaniya-uslug.html", "УНП 192308594"),
        ("/karta-sajta.html", "Карта сайта"),
        ("/karty-identifikacii-opasnostej-ocenki-riskov/", "грузчика"),
    ],
)
def test_page_ok(imported: JoomlaImporter, client: Client, path: str, text: str) -> None:
    resp = client.get(path)
    assert resp.status_code == 200, path
    assert text in resp.content.decode()


def test_canonical_without_query(imported: JoomlaImporter, client: Client) -> None:
    html = client.get("/o-nas.html?utm_source=ya&gclid=1").content.decode()
    assert '<link rel="canonical" href="https://suot.by/o-nas.html">' in html


def test_hits_incremented(imported: JoomlaImporter, client: Client) -> None:
    m = Material.objects.get(legacy_id="184")
    client.get(m.path)
    m2 = Material.objects.get(pk=m.pk)
    assert m2.hits == m.hits + 1


def test_unpublished_is_404(imported: JoomlaImporter, client: Client) -> None:
    Material.objects.filter(legacy_id="96").update(is_published=False)
    assert (
        client.get("/obyazannosti-specialista-po-ohrane-truda-nakazanie-ili-blago.html").status_code
        == 404
    )


def test_real_404(seeded: None, client: Client) -> None:
    resp = client.get("/net-takoj-stranicy.html")
    assert resp.status_code == 404
    assert "Такой страницы нет" in resp.content.decode()


def test_category_search_sort_and_pagination(imported: JoomlaImporter, client: Client) -> None:
    resp = client.get("/organizaciya-raboty-po-ohrane-truda/?q=инструктаж&sort=alpha")
    assert "внеплановый" in resp.content.decode()
    resp = client.get("/prikazy-po-ohrane-truda/?sort=bad&page=99")
    assert resp.status_code == 200
    assert "noindex" in client.get("/stati/?q=x").content.decode()


def test_search_page(imported: JoomlaImporter, client: Client) -> None:
    html = client.get("/poisk/?q=инструктажи").content.decode()
    assert "внеплановый" in html
    assert "noindex" in html
    assert client.get("/poisk/").status_code == 200


def test_home_shows_db_blocks(imported: JoomlaImporter, client: Client) -> None:
    Material.objects.filter(legacy_id="75").update(is_featured=True)
    PriceItem.objects.filter(kind="tariff").update(price="от 500")
    html = client.get("/").content.decode()
    assert "Сертификация системы управления" in html
    assert "от 500 BYN" in html
    assert "Популярное в «Вопрос-ответ»" in html


def test_about_and_clients_optional_blocks(imported: JoomlaImporter, client: Client) -> None:
    assert "Команда" not in client.get("/o-nas.html").content.decode()
    TeamMember.objects.create(name="Пётр Петров", position="Инженер")
    Testimonial.objects.create(text="Спасибо", author="Иван", organization="ООО", is_published=True)
    assert "Пётр Петров" in client.get("/o-nas.html").content.decode()
    assert "«Спасибо»" in client.get("/nashi-klienty.html").content.decode()


def test_service_page_shows_price_and_faq(imported: JoomlaImporter, client: Client) -> None:
    m = Material.objects.get(legacy_id="71")
    m.price_from = 300
    m.price_unit = "/мес"
    m.save()
    m.service_faqs.create(question="Сколько длится договор?", answer="<p>Год</p>")
    html = client.get(m.path).content.decode()
    assert "от 300 BYN/мес" in html
    assert "Сколько длится договор?" in html
    assert '"@type": "Service"' in html
