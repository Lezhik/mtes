"""Tokenization policy per Mapping Specification §15."""

import re

import tiktoken

ENCODING_NAME = "cl100k_base"
_URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
_UNICODE_QUOTE_MAP = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
    }
)


def normalize_text(text: str) -> str:
    """Normalize text before tokenization and metrics."""
    without_urls = _URL_PATTERN.sub("", text)
    return without_urls.translate(_UNICODE_QUOTE_MAP).strip()


def get_encoding() -> tiktoken.Encoding:
    return tiktoken.get_encoding(ENCODING_NAME)


def tokenize(text: str) -> list[str]:
    """Return string tokens using tiktoken cl100k_base."""
    normalized = normalize_text(text)
    encoding = get_encoding()
    token_bytes = encoding.encode(normalized)
    return [encoding.decode_single_token_bytes(token_id).decode("utf-8", errors="replace") for token_id in token_bytes]


def count_tokens(text: str) -> int:
    normalized = normalize_text(text)
    return len(get_encoding().encode(normalized))
