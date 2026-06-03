"""LLM request and response types."""

from dataclasses import dataclass, field
from typing import Any

from mtes.llm.decoding_profiles import DecodingProfile, LlmPhase


@dataclass(frozen=True, slots=True)
class LlmRequest:
    phase: LlmPhase
    system_prompt: str
    user_prompt: str
    decoding_profile: DecodingProfile
    request_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LlmResponse:
    content: str
    provider_name: str
    model_name: str
    phase: LlmPhase
    is_fallback: bool = False
    fallback_provider: str | None = None
    fallback_model: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
