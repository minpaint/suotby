# tests/test_models.py — модели контента и настроек
import pytest
from django.core.exceptions import ValidationError

from apps.content.models import Category, Material, validate_path
from apps.core.models import Client, SiteSettings, TeamMember, Testimonial
from tests.factories import CategoryFactory, MaterialFactory

pytestmark = pytest.mark.django_db


def test_material_default_path_and_sanitized() -> None:
    m = MaterialFactory(
        slug="test-slug", body="<p>ok</p><script>bad()</script>", short_answer="<b>Да</b>"
    )
    assert m.path == "/test-slug.html"
    assert "script" not in m.body
    assert m.short_answer == "Да"
    assert m.get_absolute_url() == "/test-slug.html"
    assert "ok" in m.search_text


def test_material_search_vector_filled() -> None:
    m = MaterialFactory(title="Внеплановый инструктаж")
    m.refresh_from_db()
    assert m.search_vector is not None


def test_material_properties() -> None:
    m = MaterialFactory(type=Material.Type.ORDER_SAMPLE, meta_title="")
    assert m.is_document and not m.is_question
    assert m.seo_title == m.title
    assert m.reading_minutes == 1
    assert m.file_ext == ""
    q = MaterialFactory(type=Material.Type.REQUIREMENT)
    assert q.is_question


def test_material_clean_rejects_category_path() -> None:
    CategoryFactory(slug="razdel-x", path="/razdel-x.html")
    m = Material(title="x", slug="razdel-x", type=Material.Type.PAGE)
    with pytest.raises(ValidationError):
        m.clean()


def test_published_queryset_hides_unpublished() -> None:
    MaterialFactory(is_published=False)
    visible = MaterialFactory()
    assert list(Material.objects.published()) == [visible]


@pytest.mark.parametrize(
    "path", ["/a.html", "/razdel/", "/pages/more-pages/x.html", "/a.-b/", "/kotlovkotlov.html"]
)
def test_validate_path_ok(path: str) -> None:
    validate_path(path)


@pytest.mark.parametrize("path", ["a.html", "/Кириллица.html", "/a b.html", "/a.php"])
def test_validate_path_bad(path: str) -> None:
    with pytest.raises(ValidationError):
        validate_path(path)


def test_category_empty_path_becomes_null_and_description_cleaned() -> None:
    c = Category.objects.create(
        title="Г",
        slug="g",
        path="",
        kind=Category.Kind.SERVICES_OT,
        description="<p>x</p><script>y</script>",
    )
    assert c.path is None
    assert "script" not in c.description
    assert c.get_absolute_url() == "/"
    assert c.short_title == "Г"


def test_site_settings_singleton_and_helpers() -> None:
    s = SiteSettings.load()
    s.privacy_policy = "<p>Политика</p><script>x</script>"
    s.save()
    other = SiteSettings(brand="Другой")
    other.save()
    assert SiteSettings.objects.count() == 1
    loaded = SiteSettings.load()
    assert "script" not in loaded.privacy_policy
    assert loaded.phones[0].startswith("+375")
    assert SiteSettings.tel_href("+375 29 357-09-11") == "tel:+375293570911"
    assert str(loaded) == "Настройки сайта"


def test_str_methods() -> None:
    assert str(Client.objects.create(name="ООО «А»")) == "ООО «А»"
    assert (
        str(Testimonial.objects.create(text="t", author="Иван", organization="ООО")) == "Иван — ООО"
    )
    assert str(TeamMember.objects.create(name="Пётр")) == "Пётр"
