"""Decoding profiles per LLM Interaction Specification §5."""

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class DecodingProfile:
    temperature: float
    top_p: float
    presence_penalty: float
    frequency_penalty: float


class LlmPhase(StrEnum):
    P3 = "P3"
    P4 = "P4"
    P5 = "P5"
    P6 = "P6"
    P7 = "P7"


P3_DECODING_PROFILE = DecodingProfile(
    temperature=0.20,
    top_p=0.80,
    presence_penalty=0.00,
    frequency_penalty=0.00,
)

P4_DECODING_PROFILE = DecodingProfile(
    temperature=0.60,
    top_p=0.95,
    presence_penalty=0.10,
    frequency_penalty=0.10,
)

P5_DECODING_PROFILE = DecodingProfile(
    temperature=0.80,
    top_p=0.95,
    presence_penalty=0.30,
    frequency_penalty=0.20,
)

P6_DECODING_PROFILE = DecodingProfile(
    temperature=0.00,
    top_p=0.10,
    presence_penalty=0.00,
    frequency_penalty=0.00,
)


def decoding_profile_for_phase(phase: LlmPhase) -> DecodingProfile:
    mapping = {
        LlmPhase.P3: P3_DECODING_PROFILE,
        LlmPhase.P4: P4_DECODING_PROFILE,
        LlmPhase.P5: P5_DECODING_PROFILE,
        LlmPhase.P6: P6_DECODING_PROFILE,
        LlmPhase.P7: P3_DECODING_PROFILE,
    }
    return mapping[phase]
