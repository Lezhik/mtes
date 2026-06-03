"""Dictionary and coordinate services per GA Specification §4–5."""

from dataclasses import dataclass
from pathlib import Path
import json
import math

Coordinate = tuple[int, int, int, int, int]
AXIS_CORRELATION_WARNING_THRESHOLD = 0.50
BUCKET_OVERSIZED_THRESHOLD = 20


@dataclass(frozen=True, slots=True)
class DictionaryTerm:
    token: str
    coordinate: Coordinate
    bucket_id: str
    axis_scores: tuple[float, float, float, float, float] | None = None


@dataclass(frozen=True, slots=True)
class AxisCorrelationReport:
    max_absolute_correlation: float
    warning: bool
    pairs_over_threshold: tuple[str, ...]


class DictionaryService:
    """In-memory dictionary lookup and coordinate resolution."""

    def __init__(self, terms: list[DictionaryTerm], *, dictionary_version: str) -> None:
        self._dictionary_version = dictionary_version
        self._by_token = {term.token: term for term in terms}
        self._by_coordinate: dict[Coordinate, list[DictionaryTerm]] = {}
        for term in terms:
            self._by_coordinate.setdefault(term.coordinate, []).append(term)

    @property
    def dictionary_version(self) -> str:
        return self._dictionary_version

    def lookup_token(self, token: str) -> DictionaryTerm | None:
        return self._by_token.get(token)

    def terms_at_coordinate(self, coordinate: Coordinate) -> tuple[DictionaryTerm, ...]:
        return tuple(self._by_coordinate.get(coordinate, ()))

    def resolve_anchor(self, coordinate: Coordinate) -> str:
        """Resolve anchor token for a semantic coordinate (first term at bucket)."""
        terms = self.terms_at_coordinate(coordinate)
        if not terms:
            raise KeyError(f"No dictionary term for coordinate {coordinate}")
        return min(terms, key=lambda term: term.token).token

    def bucket_term_count(self, bucket_id: str) -> int:
        return sum(1 for term in self._by_token.values() if term.bucket_id == bucket_id)

    def oversized_bucket_ids(self) -> tuple[str, ...]:
        """GA §5.4: buckets with more than 20 tokens."""
        counts: dict[str, int] = {}
        for term in self._by_token.values():
            counts[term.bucket_id] = counts.get(term.bucket_id, 0) + 1
        return tuple(
            bucket_id
            for bucket_id, count in counts.items()
            if count > BUCKET_OVERSIZED_THRESHOLD
        )

    def sparse_bucket_ids(self, *, minimum_terms: int = 5) -> tuple[str, ...]:
        counts: dict[str, int] = {}
        for term in self._by_token.values():
            counts[term.bucket_id] = counts.get(term.bucket_id, 0) + 1
        return tuple(
            bucket_id for bucket_id, count in counts.items() if count < minimum_terms
        )

    def compute_axis_correlation_report(self) -> AxisCorrelationReport | None:
        """GA §4.2: Pearson correlation warning when |r| >= 0.50."""
        scored_terms = [term for term in self._by_token.values() if term.axis_scores is not None]
        if len(scored_terms) < 2:
            return None

        axis_count = 5
        max_abs = 0.0
        flagged: list[str] = []
        for axis_a in range(axis_count):
            for axis_b in range(axis_a + 1, axis_count):
                values_a = [term.axis_scores[axis_a] for term in scored_terms if term.axis_scores]
                values_b = [term.axis_scores[axis_b] for term in scored_terms if term.axis_scores]
                correlation = _pearson_correlation(values_a, values_b)
                abs_correlation = abs(correlation)
                if abs_correlation > max_abs:
                    max_abs = abs_correlation
                if abs_correlation >= AXIS_CORRELATION_WARNING_THRESHOLD:
                    flagged.append(f"axis_{axis_a}_axis_{axis_b}")

        return AxisCorrelationReport(
            max_absolute_correlation=max_abs,
            warning=max_abs >= AXIS_CORRELATION_WARNING_THRESHOLD,
            pairs_over_threshold=tuple(flagged),
        )


def _pearson_correlation(values_a: list[float], values_b: list[float]) -> float:
    if len(values_a) != len(values_b) or len(values_a) < 2:
        return 0.0
    mean_a = sum(values_a) / len(values_a)
    mean_b = sum(values_b) / len(values_b)
    covariance = sum((a - mean_a) * (b - mean_b) for a, b in zip(values_a, values_b, strict=True))
    variance_a = sum((a - mean_a) ** 2 for a in values_a)
    variance_b = sum((b - mean_b) ** 2 for b in values_b)
    if variance_a == 0.0 or variance_b == 0.0:
        return 0.0
    return covariance / math.sqrt(variance_a * variance_b)


def load_dictionary_from_json(path: Path, *, dictionary_version: str) -> DictionaryService:
    raw_terms = json.loads(path.read_text(encoding="utf-8"))
    terms: list[DictionaryTerm] = []
    for entry in raw_terms:
        coordinate_tuple = tuple(entry["coordinate"])
        if len(coordinate_tuple) != 5:
            raise ValueError(f"Invalid coordinate length for token {entry['token']}")
        axis_scores = entry.get("axis_scores")
        parsed_scores = tuple(axis_scores) if axis_scores is not None else None
        terms.append(
            DictionaryTerm(
                token=entry["token"],
                coordinate=coordinate_tuple,  # type: ignore[arg-type]
                bucket_id=entry["bucket_id"],
                axis_scores=parsed_scores,  # type: ignore[arg-type]
            )
        )
    return DictionaryService(terms, dictionary_version=dictionary_version)
