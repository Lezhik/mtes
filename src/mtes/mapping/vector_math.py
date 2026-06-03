"""Vector math helpers for mapping pipeline."""

import math


def cosine_similarity(vector_a: tuple[float, ...], vector_b: tuple[float, ...]) -> float:
    if len(vector_a) != len(vector_b) or not vector_a:
        return 0.0
    dot = sum(a * b for a, b in zip(vector_a, vector_b, strict=True))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def cosine_distance(vector_a: tuple[float, ...], vector_b: tuple[float, ...]) -> float:
    return 1.0 - cosine_similarity(vector_a, vector_b)
