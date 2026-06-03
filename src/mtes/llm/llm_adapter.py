"""LLM provider adapter protocol and implementations."""

import asyncio
from typing import Protocol

from mtes.llm.types import LlmRequest, LlmResponse
from mtes.shared.exceptions import ProviderUnavailableError


class LlmProviderAdapter(Protocol):
    """Single LLM provider contract."""

    @property
    def provider_name(self) -> str:
        ...

    @property
    def model_name(self) -> str:
        ...

    async def complete(
        self,
        request: LlmRequest,
        *,
        timeout_seconds: float,
    ) -> LlmResponse:
        ...


def normalize_response_content(content: str) -> str:
    """Strip provider-specific whitespace while preserving payload text."""
    return content.strip()


class MockLlmProviderAdapter:
    """Deterministic mock provider for tests."""

    def __init__(
        self,
        *,
        provider_name: str,
        model_name: str,
        response_content: str,
        should_fail: bool = False,
        delay_seconds: float = 0.0,
    ) -> None:
        self._provider_name = provider_name
        self._model_name = model_name
        self._response_content = response_content
        self._should_fail = should_fail
        self._delay_seconds = delay_seconds

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model_name(self) -> str:
        return self._model_name

    async def complete(
        self,
        request: LlmRequest,
        *,
        timeout_seconds: float,
    ) -> LlmResponse:
        del timeout_seconds
        if self._delay_seconds > 0:
            await asyncio.sleep(self._delay_seconds)
        if self._should_fail:
            raise ProviderUnavailableError(f"{self._provider_name} unavailable")
        return LlmResponse(
            content=normalize_response_content(self._response_content),
            provider_name=self._provider_name,
            model_name=self._model_name,
            phase=request.phase,
            is_fallback=False,
            raw_payload={"mock": True},
        )
