"""Tests for numeric gene LUT."""

import pytest

from mtes.mapping.numeric_lut import (
    ROUND_TRIP_MAX_BYTE_ERROR,
    byte_to_gene_value,
    gene_value_to_byte,
    round_trip_byte_error,
    verify_lut_checkpoints,
)
from mtes.mapping.translation_service import (
    MVP_NUMERIC_DEFAULTS,
    anchor_similarity_threshold,
    compression_token_limit,
    translate_numeric_genes,
)


def test_lut_checkpoints_match_ga_spec() -> None:
    verify_lut_checkpoints()
    assert byte_to_gene_value(0) == pytest.approx(0.223, abs=0.006)
    assert byte_to_gene_value(128) == pytest.approx(0.501, abs=0.006)
    assert byte_to_gene_value(255) == pytest.approx(0.777, abs=0.006)


@pytest.mark.parametrize("gene_value", [0.0, 0.223, 0.501, 0.777, 1.0])
def test_round_trip_byte_error_within_one(gene_value: float) -> None:
    assert round_trip_byte_error(gene_value) <= ROUND_TRIP_MAX_BYTE_ERROR


def test_lut_is_strictly_monotonic() -> None:
    previous = byte_to_gene_value(0)
    for byte_value in range(1, 256):
        current = byte_to_gene_value(byte_value)
        assert current > previous
        previous = current


def test_compression_token_limits() -> None:
    assert compression_token_limit(0.20) == 48
    assert compression_token_limit(0.30) == 48
    assert compression_token_limit(0.55) == 36
    assert compression_token_limit(0.60) == 36
    assert compression_token_limit(0.61) == 24


def test_anchor_similarity_threshold_mvp_default() -> None:
    threshold = anchor_similarity_threshold(MVP_NUMERIC_DEFAULTS.anchor_rigidity)
    assert threshold == pytest.approx(0.82 + 0.70 * 0.14, abs=1e-6)


def test_translate_mvp_defaults() -> None:
    constraints = translate_numeric_genes(MVP_NUMERIC_DEFAULTS)
    assert constraints.target_token_limit == 36
    assert constraints.semantic_expansion_radius == 0.35
    assert constraints.punctuation_density == 0.50
