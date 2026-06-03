"""Atomic metric primitives per Mapping Specification §14."""

import re
from collections import Counter

from mtes.mapping.tokenization import normalize_text, tokenize

PUNCTUATION_CHARS = {".", ",", "!", "?", ";", ":", "—", "…"}
CLAUSE_SEPARATORS = {".", ",", ";", ":", "—"}
SHORT_CLAUSE_MAX_TOKENS = 5
INDIRECT_TOKENS = frozenset(
    {
        "someone",
        "something",
        "somewhere",
        "it",
        "they",
        "that",
        "those",
        "maybe",
        "somehow",
    }
)
ENGLISH_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "with",
        "as",
        "by",
        "from",
        "that",
        "this",
        "it",
        "not",
    }
)
_WORD_PATTERN = re.compile(r"[A-Za-z0-9']+|[#@][A-Za-z0-9_]+")


def _lexical_tokens(text: str) -> list[str]:
    normalized = normalize_text(text).lower()
    return _WORD_PATTERN.findall(normalized)


def punctuation_density(text: str) -> float:
    """Mapping Spec §14.1: punctuation_tokens / total_tokens."""
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    punctuation_count = 0
    for token in tokens:
        punctuation_count += sum(1 for char in token if char in PUNCTUATION_CHARS)
    return punctuation_count / len(tokens)


def short_clause_ratio(text: str) -> float:
    """Mapping Spec §14.2: short_clauses / total_clauses."""
    normalized = normalize_text(text)
    if not normalized:
        return 0.0

    clauses = re.split(r"([.,;:\u2014\u2014])", normalized)
    merged_clauses: list[str] = []
    buffer = ""
    for part in clauses:
        if part in CLAUSE_SEPARATORS:
            if buffer.strip():
                merged_clauses.append(buffer.strip())
            buffer = ""
        else:
            buffer += part
    if buffer.strip():
        merged_clauses.append(buffer.strip())

    if not merged_clauses:
        merged_clauses = [normalized]

    short_count = 0
    for clause in merged_clauses:
        clause_tokens = _lexical_tokens(clause)
        if len(clause_tokens) <= SHORT_CLAUSE_MAX_TOKENS:
            short_count += 1
    return short_count / len(merged_clauses)


def redundancy_penalty(text: str) -> float:
    """Mapping Spec §11.3 / v5.0: repeated_bigram_count / max(total_bigrams, 1)."""
    words = _lexical_tokens(text)
    if len(words) < 2:
        return 0.0
    bigrams = [tuple(words[index : index + 2]) for index in range(len(words) - 1)]
    counts = Counter(bigrams)
    repeated = sum(count - 1 for count in counts.values() if count > 1)
    return repeated / max(len(bigrams), 1)


def information_density(text: str) -> float:
    """Mapping Spec v5.0 §6: unique_content_lemmas / total_content_tokens."""
    words = _lexical_tokens(text)
    content_tokens = [word for word in words if word not in ENGLISH_STOPWORDS]
    if not content_tokens:
        return 0.0
    unique_lemmas = set(content_tokens)
    return len(unique_lemmas) / len(content_tokens)


def indirect_reference_ratio(text: str) -> float:
    """Mapping Spec §14.4."""
    words = _lexical_tokens(text)
    if not words:
        return 0.0
    indirect_count = sum(1 for word in words if word in INDIRECT_TOKENS)
    return indirect_count / len(words)


def compression_score(text: str) -> float:
    """Mapping Spec v5.0: clamp(information_density - redundancy_penalty, 0, 1)."""
    score = information_density(text) - redundancy_penalty(text)
    return max(0.0, min(1.0, score))
