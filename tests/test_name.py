"""Tests for Kind.NAME: strict per-component person-name comparison."""

import unicodedata

import pytest

from vi_textmatch import Kind, compare
from vi_textmatch.cli import main


@pytest.mark.parametrize(
    "a, b",
    [
        ("Phạm Quốc Khánh", "Phạm Quốc Kháng"),
        ("Nguyễn Văn An", "Nguyễn Văn Ân"),
        ("Nguyễn Thị Thu Hà", "Nguyễn Thị Thu Hằng"),
        ("Vũ Hoàng Nam", "Vũ Hoàng Nga"),
        ("Lê Văn Hoàn", "Lê Văn Hòa"),
        ("Phạm Minh Khôi", "Bùi Minh Khôi"),
        ("Nguyễn Văn An", "Nguyen Van An"),
        ("Trịnh Công Sơnn", "Trịnh Công Sơn"),
    ],
)
def test_name_one_mark_or_letter_apart_is_different(a: str, b: str) -> None:
    v = compare(a, b, kind=Kind.NAME)
    assert v.match is False
    assert v.level == "DIFFERENT"


def test_name_text_kind_still_calls_it_typo() -> None:
    """Regression anchor: the reason NAME exists."""
    assert compare("Phạm Quốc Khánh", "Phạm Quốc Kháng", kind=Kind.TEXT).level == "TYPO"


def test_name_reports_differing_position() -> None:
    v = compare("Nguyễn Văn An", "Nguyễn Văn Ân", kind=Kind.NAME)
    assert v.detail == "Name components differ at position 3"


def test_name_component_count_mismatch() -> None:
    v = compare("Nguyễn Văn An", "Nguyễn An", kind=Kind.NAME)
    assert v.match is False
    assert "count" in v.detail


@pytest.mark.parametrize(
    "a, b",
    [
        ("Nguyễn Văn An", unicodedata.normalize("NFD", "Nguyễn Văn An")),
        ("NGUYỄN VĂN AN", "Nguyễn  Văn An"),
        (" Nguyễn Văn\tAn ", "nguyễn văn an"),
        ("Bùi Minh​ Châu", "Bùi Minh Châu"),
        ("Hoà Văn Bình", "Hòa Văn Bình"),
    ],
)
def test_name_equal_when_only_form_space_case_differ(a: str, b: str) -> None:
    v = compare(a, b, kind=Kind.NAME)
    assert v.match is True
    assert v.level == "IDENTICAL"


def test_name_rejects_non_string() -> None:
    with pytest.raises(ValueError):
        compare("An", None, kind=Kind.NAME)  # type: ignore[arg-type]


def test_cli_kind_name(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["compare", "--kind", "name", "Nguyễn Văn An", "Nguyễn Văn Ân"])
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "DIFFERENT" in out
    assert "thành phần thứ 3" in out
