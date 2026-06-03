"""Tests for LLM provider chain and adapter service."""

from typing import Any

import pytest

from mtes.llm.decoding_profiles import LlmPhase, P4_DECODING_PROFILE, decoding_profile_for_phase
from mtes.llm.llm_adapter import MockLlmProviderAdapter
from mtes.llm.provider_chain import LlmAdapterService, LlmProviderChain
from mtes.llm.types import LlmRequest
from mtes.shared.exceptions import ProviderUnavailableError


class InMemoryAuditWriter:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def write_llm_audit_event(self, *, event_type: str, details: dict[str, Any]) -> None:
        self.events.append({"event_type": event_type, "details": details})


class InMemorySystemEventWriter:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def write_provider_failover(self, *, message: str, details: dict[str, Any]) -> None:
        self.events.append({"message": message, "details": details})


@pytest.mark.asyncio
async def test_primary_provider_success() -> None:
    service = LlmAdapterService(
        LlmProviderChain(
            primary=MockLlmProviderAdapter(
                provider_name="primary",
                model_name="gpt-test",
                response_content='{"candidate_text":"hello"}',
            )
        ),
        audit_log_writer=InMemoryAuditWriter(),
    )
    response = await service.complete(
        LlmRequest(
            phase=LlmPhase.P4,
            system_prompt="system",
            user_prompt="user",
            decoding_profile=P4_DECODING_PROFILE,
        )
    )
    assert response.content == '{"candidate_text":"hello"}'
    assert response.is_fallback is False


@pytest.mark.asyncio
async def test_failover_to_secondary_records_system_event() -> None:
    audit_writer = InMemoryAuditWriter()
    system_writer = InMemorySystemEventWriter()
    service = LlmAdapterService(
        LlmProviderChain(
            primary=MockLlmProviderAdapter(
                provider_name="primary",
                model_name="primary-model",
                response_content="unused",
                should_fail=True,
            ),
            secondary=MockLlmProviderAdapter(
                provider_name="secondary",
                model_name="secondary-model",
                response_content='{"ok":true}',
            ),
        ),
        audit_log_writer=audit_writer,
        system_event_writer=system_writer,
    )
    response = await service.complete(
        LlmRequest(
            phase=LlmPhase.P3,
            system_prompt="system",
            user_prompt="user",
            decoding_profile=decoding_profile_for_phase(LlmPhase.P3),
        )
    )
    assert response.provider_name == "secondary"
    assert response.is_fallback is True
    assert len(system_writer.events) == 1
    assert system_writer.events[0]["details"]["to_provider"] == "secondary"
    event_types = [event["event_type"] for event in audit_writer.events]
    assert "LLM_REQUEST" in event_types
    assert "LLM_RESPONSE" in event_types


@pytest.mark.asyncio
async def test_all_providers_fail_raises() -> None:
    service = LlmAdapterService(
        LlmProviderChain(
            primary=MockLlmProviderAdapter(
                provider_name="primary",
                model_name="m1",
                response_content="x",
                should_fail=True,
            ),
            secondary=MockLlmProviderAdapter(
                provider_name="secondary",
                model_name="m2",
                response_content="x",
                should_fail=True,
            ),
        ),
    )
    with pytest.raises(ProviderUnavailableError):
        await service.complete(
            LlmRequest(
                phase=LlmPhase.P4,
                system_prompt="s",
                user_prompt="u",
                decoding_profile=P4_DECODING_PROFILE,
            )
        )
