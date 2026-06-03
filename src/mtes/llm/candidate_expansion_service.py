"""P5 candidate expansion and ranking per LLM Interaction Specification §9."""

import json
import statistics
from dataclasses import dataclass
from typing import Any, Protocol

from mtes.llm.decoding_profiles import LlmPhase, decoding_profile_for_phase
from mtes.llm.provider_chain import LlmAdapterService
from mtes.llm.types import LlmRequest
from mtes.mapping.vector_math import cosine_distance
from mtes.shared.exceptions import ConstraintViolationError

P5_CANDIDATE_COUNT = 5

OVERALL_SCORE_WEIGHTS = {
    "constraint": 0.50,
    "diversity": 0.30,
    "quality": 0.20,
}


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    candidate_text: str
    constraint_score: float
    diversity_score: float
    quality_score: float
    overall_score: float
    selected: bool = False


class CandidateArchiveRepository(Protocol):
    async def save_ranked_candidate(
        self,
        *,
        genome_id: str,
        candidate: RankedCandidate,
        routing_family: str,
        prompt_version: str,
    ) -> str:
        ...


def token_set(text: str) -> set[str]:
    return set(text.lower().split())


def token_set_distance(text_a: str, text_b: str) -> float:
    set_a = token_set(text_a)
    set_b = token_set(text_b)
    if not set_a and not set_b:
        return 0.0
    union = set_a | set_b
    if not union:
        return 0.0
    intersection = set_a & set_b
    return 1.0 - (len(intersection) / len(union))


def constraint_score(
    candidate_text: str,
    constraint_set: dict[str, Any],
) -> float:
    constraints = constraint_set.get("generation_constraints", [])
    if not constraints:
        return 1.0
    satisfied = 0
    for constraint in constraints:
        if constraint.get("type") != "required":
            satisfied += 1
            continue
        value = str(constraint.get("value", "")).lower()
        if value and value in candidate_text.lower():
            satisfied += 1
    return satisfied / len(constraints)


def diversity_score(
    candidate_text: str,
    *,
    base_text: str,
    base_embedding: tuple[float, ...],
    candidate_embedding: tuple[float, ...],
) -> float:
    embedding_distance = cosine_distance(base_embedding, candidate_embedding)
    jaccard_distance = token_set_distance(candidate_text, base_text)
    return 0.70 * embedding_distance + 0.30 * jaccard_distance


def quality_score_stub(_candidate_text: str) -> float:
    """Placeholder until judge/coherence metrics are implemented."""
    return 0.75


def overall_score(constraint: float, diversity: float, quality: float) -> float:
    return (
        OVERALL_SCORE_WEIGHTS["constraint"] * constraint
        + OVERALL_SCORE_WEIGHTS["diversity"] * diversity
        + OVERALL_SCORE_WEIGHTS["quality"] * quality
    )


def apply_outlier_policy(candidates: list[RankedCandidate]) -> list[RankedCandidate]:
    """Mapping Spec v5.0 outlier rejection when candidate_count >= 4."""
    if len(candidates) < 4:
        return candidates
    scores = [candidate.overall_score for candidate in candidates]
    mean_score = statistics.mean(scores)
    std_score = statistics.pstdev(scores) if len(scores) > 1 else 0.0
    threshold = mean_score + 2 * std_score
    filtered = [candidate for candidate in candidates if candidate.overall_score <= threshold]
    if not filtered:
        return [max(candidates, key=lambda item: item.overall_score)]
    return filtered


class CandidateExpansionService:
    """Generate and rank P5 candidate alternatives."""

    def __init__(
        self,
        llm_adapter_service: LlmAdapterService,
        *,
        archive_repository: CandidateArchiveRepository | None = None,
        prompt_version: str = "3.1",
    ) -> None:
        self._llm_adapter_service = llm_adapter_service
        self._archive_repository = archive_repository
        self._prompt_version = prompt_version

    async def expand_candidates(
        self,
        *,
        genome_id: str,
        base_candidate_text: str,
        constraint_set: dict[str, Any],
        routing_family: str,
        base_embedding: tuple[float, ...],
        candidate_embeddings: list[tuple[float, ...]],
        llm_responses: list[str] | None = None,
    ) -> list[RankedCandidate]:
        if llm_responses is None:
            llm_responses = await self._generate_candidate_texts(
                genome_id=genome_id,
                base_candidate_text=base_candidate_text,
                constraint_set=constraint_set,
                routing_family=routing_family,
            )

        if len(llm_responses) != P5_CANDIDATE_COUNT:
            raise ConstraintViolationError(
                f"P5 requires exactly {P5_CANDIDATE_COUNT} candidates, got {len(llm_responses)}"
            )

        ranked: list[RankedCandidate] = []
        for index, text in enumerate(llm_responses):
            embedding = (
                candidate_embeddings[index]
                if index < len(candidate_embeddings)
                else base_embedding
            )
            constraint = constraint_score(text, constraint_set)
            diversity = diversity_score(
                text,
                base_text=base_candidate_text,
                base_embedding=base_embedding,
                candidate_embedding=embedding,
            )
            quality = quality_score_stub(text)
            ranked.append(
                RankedCandidate(
                    candidate_text=text,
                    constraint_score=constraint,
                    diversity_score=diversity,
                    quality_score=quality,
                    overall_score=overall_score(constraint, diversity, quality),
                )
            )

        filtered = apply_outlier_policy(ranked)
        filtered.sort(key=lambda item: (-item.overall_score, item.candidate_text))
        winner = filtered[0]
        results: list[RankedCandidate] = []
        for candidate in filtered:
            selected = candidate.candidate_text == winner.candidate_text
            final_candidate = RankedCandidate(
                candidate_text=candidate.candidate_text,
                constraint_score=candidate.constraint_score,
                diversity_score=candidate.diversity_score,
                quality_score=candidate.quality_score,
                overall_score=candidate.overall_score,
                selected=selected,
            )
            results.append(final_candidate)
            if self._archive_repository is not None:
                await self._archive_repository.save_ranked_candidate(
                    genome_id=genome_id,
                    candidate=final_candidate,
                    routing_family=routing_family,
                    prompt_version=self._prompt_version,
                )
        return results

    async def _generate_candidate_texts(
        self,
        *,
        genome_id: str,
        base_candidate_text: str,
        constraint_set: dict[str, Any],
        routing_family: str,
    ) -> list[str]:
        request = LlmRequest(
            phase=LlmPhase.P5,
            system_prompt="Generate diverse candidate_text variants as JSON list.",
            user_prompt=json.dumps(
                {
                    "base_candidate_text": base_candidate_text,
                    "generation_constraints": constraint_set.get("generation_constraints", []),
                    "routing_family": routing_family,
                    "candidate_count": P5_CANDIDATE_COUNT,
                }
            ),
            decoding_profile=decoding_profile_for_phase(LlmPhase.P5),
            metadata={"genome_id": genome_id},
        )
        response = await self._llm_adapter_service.complete(request)
        payload = json.loads(response.content)
        if isinstance(payload, dict) and "candidates" in payload:
            candidates = payload["candidates"]
        elif isinstance(payload, list):
            candidates = payload
        else:
            raise ConstraintViolationError("P5 response must provide candidates list")
        texts: list[str] = []
        for item in candidates:
            if isinstance(item, dict) and "candidate_text" in item:
                texts.append(str(item["candidate_text"]))
            elif isinstance(item, str):
                texts.append(item)
        return texts
