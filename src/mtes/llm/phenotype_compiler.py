"""P4 phenotype compilation per LLM Interaction Specification §8."""

import json
from typing import Any, Protocol

from mtes.llm.decoding_profiles import LlmPhase, decoding_profile_for_phase
from mtes.llm.prompt_router import PromptRouter, RoutingDecision
from mtes.llm.provider_chain import LlmAdapterService
from mtes.llm.types import LlmRequest
from mtes.shared.exceptions import ConstraintViolationError
from mtes.shared.types import Genome, NumericGenes


class PhenotypeCandidateRepository(Protocol):
    async def save_raw_candidate(
        self,
        *,
        genome_id: str,
        text: str,
        routing_family: str,
        prompt_version: str,
        provider: str,
        model: str,
    ) -> str:
        ...


class PhenotypeCompiler:
    """Compile a single phenotype from validated P3 constraints."""

    def __init__(
        self,
        llm_adapter_service: LlmAdapterService,
        *,
        prompt_router: PromptRouter | None = None,
        candidate_repository: PhenotypeCandidateRepository | None = None,
        prompt_version: str = "3.1",
    ) -> None:
        self._llm_adapter_service = llm_adapter_service
        self._prompt_router = prompt_router or PromptRouter()
        self._candidate_repository = candidate_repository
        self._prompt_version = prompt_version

    def build_p4_user_prompt(
        self,
        constraint_set: dict[str, Any],
        *,
        routing: RoutingDecision,
        structural_plan: dict[str, Any] | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "generation_constraints": constraint_set.get("generation_constraints", []),
            "routing_family": routing.selected_family.value,
            "activated_families": list(routing.activated_families),
        }
        if structural_plan is not None:
            payload["structural_plan"] = structural_plan
        return json.dumps(payload, ensure_ascii=False)

    async def compile_phenotype(
        self,
        genome: Genome,
        constraint_set: dict[str, Any],
        *,
        structural_plan: dict[str, Any] | None = None,
        current_family: str | None = None,
        current_family_score: float | None = None,
    ) -> dict[str, Any]:
        from mtes.llm.prompt_router import PromptFamily

        current_enum = PromptFamily(current_family) if current_family else None
        routing = self._prompt_router.select_family(
            genome.numeric_genes,
            current_family=current_enum,
            current_family_score=current_family_score,
        )
        request = LlmRequest(
            phase=LlmPhase.P4,
            system_prompt=(
                "Compile one candidate_text JSON object. "
                "Preserve required constraints. Do not optimize engagement."
            ),
            user_prompt=self.build_p4_user_prompt(
                constraint_set,
                routing=routing,
                structural_plan=structural_plan,
            ),
            decoding_profile=decoding_profile_for_phase(LlmPhase.P4),
            metadata={
                "genome_id": genome.genome_id,
                "routing_family": routing.selected_family.value,
            },
        )
        response = await self._llm_adapter_service.complete(request)
        try:
            payload = json.loads(response.content)
        except json.JSONDecodeError as exc:
            raise ConstraintViolationError("P4 response is not valid JSON") from exc
        if not isinstance(payload, dict) or "candidate_text" not in payload:
            raise ConstraintViolationError("P4 response must contain candidate_text")

        if self._candidate_repository is not None:
            await self._candidate_repository.save_raw_candidate(
                genome_id=genome.genome_id,
                text=str(payload["candidate_text"]),
                routing_family=routing.selected_family.value,
                prompt_version=self._prompt_version,
                provider=response.provider_name,
                model=response.model_name,
            )
        return {
            "candidate_text": str(payload["candidate_text"]),
            "routing_family": routing.selected_family.value,
            "routing": routing,
            "provider": response.provider_name,
            "model": response.model_name,
        }
