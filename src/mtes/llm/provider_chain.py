"""LLM provider chain with failover, audit logging, and decoding profiles."""

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from mtes.llm.decoding_profiles import decoding_profile_for_phase
from mtes.llm.llm_adapter import LlmProviderAdapter, normalize_response_content
from mtes.llm.types import LlmRequest, LlmResponse
from mtes.shared.exceptions import ProviderUnavailableError


class AuditLogWriter(Protocol):
    async def write_llm_audit_event(
        self,
        *,
        event_type: str,
        details: dict[str, Any],
    ) -> None:
        ...


class SystemEventWriter(Protocol):
    async def write_provider_failover(
        self,
        *,
        message: str,
        details: dict[str, Any],
    ) -> None:
        ...


@dataclass(frozen=True, slots=True)
class LlmProviderChain:
    """Primary → secondary → fallback execution per SRS §13.3."""

    primary: LlmProviderAdapter
    secondary: LlmProviderAdapter | None = None
    fallback: LlmProviderAdapter | None = None
    default_timeout_seconds: float = 60.0

    def providers_in_order(self) -> tuple[LlmProviderAdapter, ...]:
        chain: list[LlmProviderAdapter] = [self.primary]
        if self.secondary is not None:
            chain.append(self.secondary)
        if self.fallback is not None:
            chain.append(self.fallback)
        return tuple(chain)


class LlmAdapterService:
    """Execute LLM requests with decoding profiles, audit trail, and failover."""

    def __init__(
        self,
        provider_chain: LlmProviderChain,
        *,
        audit_log_writer: AuditLogWriter | None = None,
        system_event_writer: SystemEventWriter | None = None,
    ) -> None:
        self._chain = provider_chain
        self._audit_log_writer = audit_log_writer
        self._system_event_writer = system_event_writer

    async def complete(
        self,
        request: LlmRequest,
        *,
        timeout_seconds: float | None = None,
    ) -> LlmResponse:
        request_with_profile = LlmRequest(
            phase=request.phase,
            system_prompt=request.system_prompt,
            user_prompt=request.user_prompt,
            decoding_profile=request.decoding_profile,
            request_id=request.request_id or str(uuid.uuid4()),
            metadata=request.metadata,
        )
        if request_with_profile.decoding_profile != decoding_profile_for_phase(request.phase):
            pass  # Caller may override; profile still attached to request.

        await self._write_audit(
            event_type="LLM_REQUEST",
            details={
                "request_id": request_with_profile.request_id,
                "phase": request_with_profile.phase.value,
                "provider_chain": [provider.provider_name for provider in self._chain.providers_in_order()],
                "decoding_profile": {
                    "temperature": request_with_profile.decoding_profile.temperature,
                    "top_p": request_with_profile.decoding_profile.top_p,
                    "presence_penalty": request_with_profile.decoding_profile.presence_penalty,
                    "frequency_penalty": request_with_profile.decoding_profile.frequency_penalty,
                },
            },
        )

        timeout = timeout_seconds or self._chain.default_timeout_seconds
        last_error: Exception | None = None
        providers = self._chain.providers_in_order()

        for index, provider in enumerate(providers):
            try:
                response = await asyncio.wait_for(
                    provider.complete(request_with_profile, timeout_seconds=timeout),
                    timeout=timeout,
                )
                normalized = LlmResponse(
                    content=normalize_response_content(response.content),
                    provider_name=response.provider_name,
                    model_name=response.model_name,
                    phase=response.phase,
                    is_fallback=index > 0,
                    fallback_provider=response.provider_name if index > 0 else None,
                    fallback_model=response.model_name if index > 0 else None,
                    raw_payload=response.raw_payload,
                )
                await self._write_audit(
                    event_type="LLM_RESPONSE",
                    details={
                        "request_id": request_with_profile.request_id,
                        "phase": request_with_profile.phase.value,
                        "provider": normalized.provider_name,
                        "model": normalized.model_name,
                        "is_fallback_output": normalized.is_fallback,
                        "fallback_provider": normalized.fallback_provider,
                        "fallback_model": normalized.fallback_model,
                    },
                )
                return normalized
            except (ProviderUnavailableError, asyncio.TimeoutError) as exc:
                last_error = exc
                if index < len(providers) - 1:
                    next_provider = providers[index + 1]
                    await self._write_failover_event(
                        from_provider=provider.provider_name,
                        to_provider=next_provider.provider_name,
                        reason=str(exc),
                    )
                continue

        await self._write_audit(
            event_type="LLM_RESPONSE",
            details={
                "request_id": request_with_profile.request_id,
                "phase": request_with_profile.phase.value,
                "status": "failed",
                "error": str(last_error),
            },
        )
        raise ProviderUnavailableError(
            f"All LLM providers failed for phase {request_with_profile.phase.value}: {last_error}"
        ) from last_error

    async def _write_audit(self, *, event_type: str, details: dict[str, Any]) -> None:
        if self._audit_log_writer is None:
            return
        await self._audit_log_writer.write_llm_audit_event(
            event_type=event_type,
            details=details,
        )

    async def _write_failover_event(
        self,
        *,
        from_provider: str,
        to_provider: str,
        reason: str,
    ) -> None:
        if self._system_event_writer is None:
            return
        await self._system_event_writer.write_provider_failover(
            message=f"failover {from_provider} -> {to_provider}",
            details={
                "from_provider": from_provider,
                "to_provider": to_provider,
                "reason": reason,
            },
        )
