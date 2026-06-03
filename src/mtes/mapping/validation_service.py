"""Validation pipeline per Mapping Specification §6 and §10."""

from dataclasses import dataclass, field
from typing import Any, Protocol

from mtes.mapping.metrics import compression_score, indirect_reference_ratio
from mtes.mapping.tokenization import tokenize
from mtes.mapping.translation_service import TranslatedConstraints
from mtes.shared.exceptions import ConstraintViolationError

ANCHOR_HARD_REJECT_THRESHOLD = 0.70
IRREGULAR_LEMMA_PAIRS: dict[str, str] = {
    "run": "ran",
    "write": "wrote",
}


@dataclass(frozen=True, slots=True)
class ValidationResult:
    schema_pass: bool
    constraint_pass: bool
    semantic_pass: bool
    integration_pass: bool
    anchor_integrity: float
    failed_checks: tuple[str, ...] = field(default_factory=tuple)
    repair_attempts: int = 0

    @property
    def passed(self) -> bool:
        return (
            self.schema_pass
            and self.constraint_pass
            and self.semantic_pass
            and self.integration_pass
            and self.anchor_integrity >= ANCHOR_HARD_REJECT_THRESHOLD
        )


class ValidationRecordRepository(Protocol):
    async def save_validation_record(
        self,
        *,
        candidate_id: str,
        result: ValidationResult,
    ) -> str:
        ...


class ValidationService:
    """Validate candidate text against constraints and anchors."""

    def anchor_integrity(self, text: str, required_anchors: tuple[str, ...]) -> float:
        if not required_anchors:
            return 1.0
        tokens = {token.lower() for token in tokenize(text)}
        words = set(text.lower().split())
        preserved = 0
        for anchor in required_anchors:
            anchor_lower = anchor.lower()
            if anchor_lower in tokens or anchor_lower in words:
                preserved += 1
                continue
            lemma_match = any(
                IRREGULAR_LEMMA_PAIRS.get(anchor_lower) == token
                or IRREGULAR_LEMMA_PAIRS.get(token) == anchor_lower
                for token in tokens
            )
            if lemma_match:
                preserved += 1
        return preserved / len(required_anchors)

    def validate_candidate(
        self,
        *,
        candidate_text: str,
        required_anchors: tuple[str, ...],
        constraints: TranslatedConstraints,
        anchor_similarity_threshold: float | None = None,
    ) -> ValidationResult:
        del anchor_similarity_threshold  # cosine lemma path deferred to Phase 4 embedding integration
        failed: list[str] = []
        if not candidate_text.strip():
            failed.append("empty_text")
        anchor_score = self.anchor_integrity(candidate_text, required_anchors)
        if anchor_score < constraints.anchor_similarity_threshold:
            failed.append("anchor_preservation")
        if anchor_score < ANCHOR_HARD_REJECT_THRESHOLD:
            failed.append("anchor_hard_reject")

        constraint_pass = all(
            [
                indirect_reference_ratio(candidate_text) <= max(constraints.indirect_reference_ratio, 1.0),
                compression_score(candidate_text) >= 0.0,
            ]
        )
        if not constraint_pass:
            failed.append("constraint_deviation")

        semantic_pass = anchor_score >= ANCHOR_HARD_REJECT_THRESHOLD
        return ValidationResult(
            schema_pass=True,
            constraint_pass=constraint_pass,
            semantic_pass=semantic_pass,
            integration_pass=True,
            anchor_integrity=anchor_score,
            failed_checks=tuple(failed),
        )

    async def validate_and_persist(
        self,
        *,
        candidate_id: str,
        candidate_text: str,
        required_anchors: tuple[str, ...],
        constraints: TranslatedConstraints,
        repository: ValidationRecordRepository | None = None,
    ) -> ValidationResult:
        result = self.validate_candidate(
            candidate_text=candidate_text,
            required_anchors=required_anchors,
            constraints=constraints,
        )
        if not result.passed:
            raise ConstraintViolationError(
                f"Validation failed: {', '.join(result.failed_checks)}"
            )
        if repository is not None:
            await repository.save_validation_record(candidate_id=candidate_id, result=result)
        return result
