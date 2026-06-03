"""P3 constraint expansion per LLM Interaction Specification §7."""

import json
from typing import Any, Protocol

from mtes.llm.constraint_schema import validate_constraint_expansion_payload
from mtes.llm.decoding_profiles import LlmPhase, decoding_profile_for_phase
from mtes.llm.provider_chain import LlmAdapterService
from mtes.llm.types import LlmRequest
from mtes.shared.exceptions import ConstraintViolationError
from mtes.shared.types import Genome


class ConstraintRecordRepository(Protocol):
    async def save_constraint_record(
        self,
        *,
        genome_id: str,
        constraint_set: dict[str, Any],
        mapping_version: str,
    ) -> str:
        ...


class ConstraintExpansionService:
    """Run P3 constraint expansion and validation before P4."""

    def __init__(
        self,
        llm_adapter_service: LlmAdapterService,
        *,
        constraint_repository: ConstraintRecordRepository | None = None,
        mapping_version: str = "4.9",
    ) -> None:
        self._llm_adapter_service = llm_adapter_service
        self._constraint_repository = constraint_repository
        self._mapping_version = mapping_version

    def build_p3_user_prompt(self, genome: Genome) -> str:
        numeric = genome.numeric_genes
        return json.dumps(
            {
                "semantic_genes": [
                    {
                        "gene_id": gene.gene_id,
                        "coordinate": list(gene.coordinate),
                        "anchor": gene.anchor,
                    }
                    for gene in genome.semantic_genes
                ],
                "numeric_genes": {
                    "fragmentation_bias": numeric.fragmentation_bias,
                    "ambiguity_bias": numeric.ambiguity_bias,
                    "sentiment_contrast": numeric.sentiment_contrast,
                    "semantic_jump_radius": numeric.semantic_jump_radius,
                    "compression_target": numeric.compression_target,
                    "anchor_rigidity": numeric.anchor_rigidity,
                },
                "active_dimensions": [
                    "anchor",
                    "fragmentation",
                    "compression",
                    "ambiguity",
                ],
            },
            ensure_ascii=False,
        )

    async def expand_constraints(self, genome: Genome) -> dict[str, Any]:
        request = LlmRequest(
            phase=LlmPhase.P3,
            system_prompt=(
                "Expand genome state into generation_constraints JSON. "
                "Do not invent new themes or anchors."
            ),
            user_prompt=self.build_p3_user_prompt(genome),
            decoding_profile=decoding_profile_for_phase(LlmPhase.P3),
            metadata={"genome_id": genome.genome_id},
        )
        response = await self._llm_adapter_service.complete(request)
        try:
            payload = json.loads(response.content)
        except json.JSONDecodeError as exc:
            raise ConstraintViolationError("P3 response is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise ConstraintViolationError("P3 response root must be an object")
        validated = validate_constraint_expansion_payload(payload)
        if self._constraint_repository is not None:
            await self._constraint_repository.save_constraint_record(
                genome_id=genome.genome_id,
                constraint_set=validated,
                mapping_version=self._mapping_version,
            )
        return validated
