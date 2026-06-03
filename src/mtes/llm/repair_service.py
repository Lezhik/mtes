"""Repair layer per Mapping Specification §10."""

from dataclasses import dataclass, field
from typing import Any

from mtes.llm.decoding_profiles import LlmPhase, decoding_profile_for_phase
from mtes.llm.provider_chain import LlmAdapterService
from mtes.llm.types import LlmRequest
from mtes.mapping.tokenization import count_tokens
from mtes.mapping.validation_service import ValidationResult
from mtes.shared.exceptions import ConstraintViolationError

MAX_REPAIR_OPERATIONS = 3
MAX_REPAIR_TOKEN_DELTA = 0.15
LEAKAGE_WINDOW_GENERATIONS = 10
LEAKAGE_WINDOW_COUNT = 3
LEAKAGE_PENALTY_THRESHOLD = 0.08


@dataclass
class RepairLeakageMonitor:
    """Track repair penalties across evaluation windows."""

    window_size: int = LEAKAGE_WINDOW_GENERATIONS
    required_consecutive_windows: int = LEAKAGE_WINDOW_COUNT
    penalty_threshold: float = LEAKAGE_PENALTY_THRESHOLD
    _window_penalties: list[float] = field(default_factory=list)
    _consecutive_high_windows: int = 0

    def record_window(self, penalties: list[float]) -> None:
        if not penalties:
            mean_penalty = 0.0
        else:
            mean_penalty = sum(penalties) / len(penalties)
        self._window_penalties.append(mean_penalty)
        if mean_penalty > self.penalty_threshold:
            self._consecutive_high_windows += 1
        else:
            self._consecutive_high_windows = 0

    def leakage_detected(self) -> bool:
        return self._consecutive_high_windows >= self.required_consecutive_windows

    def diagnostic_action(self) -> str:
        if not self.leakage_detected():
            return "none"
        return "reduce_semantic_expansion_radius"


@dataclass(frozen=True, slots=True)
class RepairResult:
    repaired_text: str
    repair_operations: int
    repair_token_delta: float
    repair_penalty: float
    diagnostic_action: str


class RepairService:
    """Bounded repair using LLM with diagnostic-first recovery hooks."""

    def __init__(self, llm_adapter_service: LlmAdapterService) -> None:
        self._llm_adapter_service = llm_adapter_service
        self._leakage_monitor = RepairLeakageMonitor()

    @property
    def leakage_monitor(self) -> RepairLeakageMonitor:
        return self._leakage_monitor

    def repair_token_delta(self, original_text: str, repaired_text: str) -> float:
        original_count = max(count_tokens(original_text), 1)
        delta_tokens = abs(count_tokens(repaired_text) - original_count)
        return delta_tokens / original_count

    async def repair_candidate(
        self,
        *,
        candidate_text: str,
        violation: str,
        validation_result: ValidationResult,
    ) -> RepairResult:
        if validation_result.repair_attempts >= MAX_REPAIR_OPERATIONS:
            raise ConstraintViolationError("repair_operations exceeds maximum")

        request = LlmRequest(
            phase=LlmPhase.P7,
            system_prompt=(
                "Repair only the violated constraint. Preserve remaining content. "
                "Maximum modification budget: 15% of tokens."
            ),
            user_prompt=f"Violation:\n{violation}\n\nCandidate:\n{candidate_text}",
            decoding_profile=decoding_profile_for_phase(LlmPhase.P7),
        )
        response = await self._llm_adapter_service.complete(request)
        repaired_text = response.content.strip()
        token_delta = self.repair_token_delta(candidate_text, repaired_text)
        if token_delta > MAX_REPAIR_TOKEN_DELTA:
            raise ConstraintViolationError("repair_token_delta exceeds 15% budget")

        repair_penalty = min(1.0, token_delta + (validation_result.repair_attempts + 1) * 0.02)
        self._leakage_monitor.record_window([repair_penalty])
        diagnostic_action = self._leakage_monitor.diagnostic_action()

        return RepairResult(
            repaired_text=repaired_text,
            repair_operations=validation_result.repair_attempts + 1,
            repair_token_delta=token_delta,
            repair_penalty=repair_penalty,
            diagnostic_action=diagnostic_action,
        )
