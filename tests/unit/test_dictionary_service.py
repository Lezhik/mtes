"""Tests for dictionary service."""

from pathlib import Path

import pytest

from mtes.mapping.dictionary_service import load_dictionary_from_json

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "dictionary_terms.json"


@pytest.fixture
def dictionary_service():
    return load_dictionary_from_json(FIXTURE_PATH, dictionary_version="4.2")


def test_resolve_anchor_from_coordinate(dictionary_service) -> None:
    anchor = dictionary_service.resolve_anchor((3, 5, 4, 2, 3))
    assert anchor == "winter"


def test_lookup_token(dictionary_service) -> None:
    term = dictionary_service.lookup_token("automation")
    assert term is not None
    assert term.coordinate == (1, 2, 6, 5, 7)


def test_resolve_anchor_unknown_coordinate_raises(dictionary_service) -> None:
    with pytest.raises(KeyError):
        dictionary_service.resolve_anchor((0, 0, 0, 0, 0))


def test_axis_correlation_report_runs(dictionary_service) -> None:
    report = dictionary_service.compute_axis_correlation_report()
    assert report is not None
    assert report.max_absolute_correlation >= 0.0
