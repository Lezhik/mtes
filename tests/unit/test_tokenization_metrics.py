"""Golden-style tests for tokenization and metrics."""

import pytest

from mtes.mapping.metrics import (
    compression_score,
    indirect_reference_ratio,
    information_density,
    punctuation_density,
    redundancy_penalty,
    short_clause_ratio,
)
from mtes.mapping.tokenization import count_tokens, normalize_text, tokenize


def test_normalize_text_removes_urls_and_quotes() -> None:
    raw = 'See https://example.com/path and “hello”'
    normalized = normalize_text(raw)
    assert "https://" not in normalized
    assert '"' in normalized or "'" in normalized


def test_tokenize_counts_punctuation_as_tokens() -> None:
    tokens = tokenize("Hello, world!")
    assert len(tokens) >= 3


def test_punctuation_density_example() -> None:
    text = "Wait... Really?"
    density = punctuation_density(text)
    assert density > 0.0


def test_short_clause_ratio_all_short() -> None:
    text = "One. Two. Three."
    ratio = short_clause_ratio(text)
    assert ratio == pytest.approx(1.0)


def test_redundancy_penalty_detects_repeated_bigram() -> None:
    text = "alpha beta alpha beta gamma"
    penalty = redundancy_penalty(text)
    assert penalty > 0.0


def test_indirect_reference_ratio() -> None:
    text = "Someone said they would maybe do it."
    ratio = indirect_reference_ratio(text)
    assert ratio > 0.0


def test_information_density_unique_words() -> None:
    text = "winter silence drifts slowly"
    density = information_density(text)
    assert density == pytest.approx(1.0)


def test_compression_score_clamped() -> None:
    text = "unique words flow forward"
    score = compression_score(text)
    assert 0.0 <= score <= 1.0


def test_count_tokens_excludes_url_before_encoding() -> None:
    with_url = count_tokens("hello https://x.test/a")
    without_url = count_tokens("hello ")
    assert with_url == without_url
