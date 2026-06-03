"""Telegram gateway for outbound publish and inbound operator commands."""

import asyncio
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol

from mtes.core.operator_auth import OperatorAuthService
from mtes.monitoring.metrics_registry import PUBLICATION_TOTAL, TELEGRAM_FAILURES_TOTAL
from mtes.shared.exceptions import TelegramGatewayUnavailableError

TELEGRAM_MESSAGES_PER_MINUTE = 30
TELEGRAM_MIN_INTERVAL_SECONDS = 60.0 / TELEGRAM_MESSAGES_PER_MINUTE


@dataclass
class TelegramRateGate:
    """SRS §8.3: throttle outbound messages to 30 per minute."""

    _last_publish_monotonic: float = 0.0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            if self._last_publish_monotonic > 0.0:
                elapsed = now - self._last_publish_monotonic
                wait_seconds = TELEGRAM_MIN_INTERVAL_SECONDS - elapsed
                if wait_seconds > 0.0:
                    await asyncio.sleep(wait_seconds)
            self._last_publish_monotonic = time.monotonic()


class OperatorCommandAction(StrEnum):
    PAUSE_EVOLUTION = "pause_evolution"
    RESUME_EVOLUTION = "resume_evolution"
    EMERGENCY_STOP = "emergency_stop"
    PUBLISH_STATUS = "publish_status"


class EvolutionPauseControl(Protocol):
    def request_pause_at_boundary(self) -> None:
        ...

    def clear_pause_request(self) -> None:
        ...


class WorkflowEmergencyControl(Protocol):
    def trigger_emergency_stop(self) -> None:
        ...


@dataclass(frozen=True, slots=True)
class TelegramInboundMessage:
    operator_id: str
    command_text: str
    chat_id: str


@dataclass(frozen=True, slots=True)
class TelegramPublishResult:
    message_id: str
    channel_id: str


class TelegramApiClient(Protocol):
    async def send_message(self, *, channel_id: str, text: str) -> str:
        """Send channel message; returns provider message id."""
        ...


@dataclass
class TelegramGateway:
    """Publish phenotypes and translate operator Telegram commands."""

    api_client: TelegramApiClient
    channel_id: str
    operator_auth: OperatorAuthService
    evolution_control: EvolutionPauseControl | None = None
    workflow_control: WorkflowEmergencyControl | None = None
    _rate_gate: TelegramRateGate = field(default_factory=TelegramRateGate)

    async def publish_text(self, text: str) -> TelegramPublishResult:
        await self._rate_gate.acquire()
        try:
            message_id = await self.api_client.send_message(channel_id=self.channel_id, text=text)
        except Exception as exc:
            TELEGRAM_FAILURES_TOTAL.inc()
            raise TelegramGatewayUnavailableError("Telegram publish failed") from exc
        PUBLICATION_TOTAL.inc()
        return TelegramPublishResult(message_id=message_id, channel_id=self.channel_id)

    def translate_operator_command(self, message: TelegramInboundMessage) -> OperatorCommandAction:
        normalized = message.command_text.strip().lower()
        mapping = {
            "/pause": OperatorCommandAction.PAUSE_EVOLUTION,
            "pause": OperatorCommandAction.PAUSE_EVOLUTION,
            "/resume": OperatorCommandAction.RESUME_EVOLUTION,
            "resume": OperatorCommandAction.RESUME_EVOLUTION,
            "/stop": OperatorCommandAction.EMERGENCY_STOP,
            "stop": OperatorCommandAction.EMERGENCY_STOP,
            "/status": OperatorCommandAction.PUBLISH_STATUS,
            "status": OperatorCommandAction.PUBLISH_STATUS,
        }
        action = mapping.get(normalized)
        if action is None:
            raise ValueError(f"Unsupported Telegram operator command: {message.command_text}")
        return action

    async def handle_operator_command(
        self,
        message: TelegramInboundMessage,
        *,
        operator_token: str | None,
    ) -> dict[str, Any]:
        self.operator_auth.authenticate(
            operator_id=message.operator_id,
            presented_token=operator_token,
        )
        action = self.translate_operator_command(message)
        self.operator_auth.audit_admin_command(
            operator_id=message.operator_id,
            command=f"telegram {action.value}",
        )
        if action == OperatorCommandAction.PAUSE_EVOLUTION and self.evolution_control is not None:
            self.evolution_control.request_pause_at_boundary()
        elif action == OperatorCommandAction.RESUME_EVOLUTION and self.evolution_control is not None:
            self.evolution_control.clear_pause_request()
        elif action == OperatorCommandAction.EMERGENCY_STOP and self.workflow_control is not None:
            self.workflow_control.trigger_emergency_stop()
        return {"action": action.value, "accepted": True}
