# tests/test_sanitize.py — санитайзер HTML против XSS
import pytest

from apps.core.sanitize import clean_html, clean_text


@pytest.mark.parametrize(
    "dirty",
    [
        "<script>alert(1)</script>",
        '<img src=x onerror="alert(1)">',
        '<a href="javascript:alert(1)">x</a>',
        "<iframe src='https://evil'></iframe>",
        "<style>body{display:none}</style>",
        '<p style="background:url(javascript:alert(1))">x</p>',
        "<svg onload=alert(1)>",
        '<div onclick="steal()">x</div>',
        "<object data='x.swf'></object>",
    ],
)
def test_xss_vectors_removed(dirty: str) -> None:
    out = clean_html(dirty).lower()
    for bad in (
        "<script",
        "onerror",
        "javascript:",
        "<iframe",
        "<style",
        "onload",
        "onclick",
        "<object",
        "style=",
    ):
        assert bad not in out


def test_keeps_tables_lists_links() -> None:
    html = '<table><tr><td colspan="2">A</td></tr></table><ul><li>x</li></ul><a href="https://ohranatruda.of.by/">l</a>'
    out = clean_html(html)
    assert 'colspan="2"' in out
    assert "<li>x</li>" in out
    assert 'rel="noopener noreferrer"' in out


def test_h1_downgraded_and_empty_paragraphs_dropped() -> None:
    out = clean_html("<h1>Заголовок</h1><p>&nbsp;</p><p><br></p><p>Текст</p>")
    assert "<h2>Заголовок</h2>" in out
    assert out.count("<p>") == 1


def test_empty_values() -> None:
    assert clean_html(None) == ""
    assert clean_html("") == ""
    assert clean_text(None) == ""


def test_clean_text_strips_tags() -> None:
    assert clean_text("<b>Коротко</b>   <script>x()</script> ответ") == "Коротко ответ"
