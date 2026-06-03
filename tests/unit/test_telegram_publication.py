"""Telegram gateway and publication service tests."""

import pytest

from mtes.core.evolution_lifecycle_service import EvolutionLifecycleService
from mtes.core.operator_auth import OperatorAuthService
from mtes.core.workflow_coordinator import WorkflowCoordinator
from mtes.publication.publication_service import PublicationService
from mtes.shared.exceptions import TelegramGatewayUnavailableError
from mtes.telegram.telegram_gateway import (
    OperatorCommandAction,
    TelegramGateway,
    TelegramInboundMessage,
)


class FakeTelegramApiClient:
    def __init__(self) -> None:
        self.sent: list[str] = []
        self.fail_next = False

    async def send_message(self, *, channel_id: str, text: str) -> str:
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("telegram unavailable")
        self.sent.append(text)
        return f"msg-{len(self.sent)}"


class InMemoryPublicationQueue:
    def __init__(self) -> None:
        self._documents: dict[str, dict[str, object]] = {}

    async def insert_one(self, document: dict[str, object]) -> str:
        queue_id = str(document["_id"])
        self._documents[queue_id] = dict(document)
        return queue_id

    async def find(self, query: dict[str, object]) -> list[dict[str, object]]:
        status = query.get("status")
        return [
            document
            for document in self._documents.values()
            if status is None or document.get("status") == status
        ]

    async def replace_one(self, document_id: str, document: dict[str, object]) -> None:
        self._documents[document_id] = dict(document)


@pytest.mark.asyncio
async def test_telegram_publish_respects_rate_limit_and_records_message() -> None:
    client = FakeTelegramApiClient()
    gateway = TelegramGateway(
        api_client=client,
        channel_id="channel",
        operator_auth=OperatorAuthService(
            allowed_operator_ids=frozenset({"op"}),
            operator_token="token",
        ),
    )
    result = await gateway.publish_text("hello world")
    assert result.message_id == "msg-1"
    assert client.sent == ["hello world"]


@pytest.mark.asyncio
async def test_operator_command_maps_to_pause_signal() -> None:
    lifecycle = EvolutionLifecycleService()
    gateway = TelegramGateway(
        api_client=FakeTelegramApiClient(),
        channel_id="channel",
        operator_auth=OperatorAuthService(
            allowed_operator_ids=frozenset({"op"}),
            operator_token="token",
        ),
        evolution_control=lifecycle,
    )
    response = await gateway.handle_operator_command(
        TelegramInboundMessage(operator_id="op", command_text="/pause", chat_id="1"),
        operator_token="token",
    )
    assert response["action"] == OperatorCommandAction.PAUSE_EVOLUTION.value
    assert lifecycle._pause_requested is True


@pytest.mark.asyncio
async def test_emergency_stop_command_triggers_workflow_flag() -> None:
    class FakeWorkflowRepo:
        async def find_by_workflow_id(self, workflow_id: str) -> dict[str, object] | None:
            return None

        async def create_workflow_state(self, workflow_id: str, *, state: str, stage: str) -> dict[str, object]:
            return {"workflow_id": workflow_id, "state": state, "stage": stage}

        async def find_active_workflows(self) -> list[dict[str, object]]:
            return []

        async def transition_workflow_state(self, **kwargs: object) -> dict[str, object] | None:
            return None

    coordinator = WorkflowCoordinator(workflow_repository=FakeWorkflowRepo())  # type: ignore[arg-type]
    gateway = TelegramGateway(
        api_client=FakeTelegramApiClient(),
        channel_id="channel",
        operator_auth=OperatorAuthService(
            allowed_operator_ids=frozenset({"op"}),
            operator_token="token",
        ),
        workflow_control=coordinator,
    )
    await gateway.handle_operator_command(
        TelegramInboundMessage(operator_id="op", command_text="/stop", chat_id="1"),
        operator_token="token",
    )
    assert coordinator.emergency_stop is True


@pytest.mark.asyncio
async def test_publication_service_processes_queue_item() -> None:
    client = FakeTelegramApiClient()
    gateway = TelegramGateway(
        api_client=client,
        channel_id="channel",
        operator_auth=OperatorAuthService(
            allowed_operator_ids=frozenset(),
            operator_token=None,
        ),
    )
    queue = InMemoryPublicationQueue()
    service = PublicationService(publication_queue=queue, telegram_gateway=gateway)
    await service.enqueue_publication(candidate_id="c1", text="tweet body")
    published = await service.process_pending_publications()
    assert published == 1
    assert client.sent == ["tweet body"]


class AlwaysFailingTelegramApiClient:
    async def send_message(self, *, channel_id: str, text: str) -> str:
        raise RuntimeError("telegram unavailable")


@pytest.mark.asyncio
async def test_publication_retries_then_marks_failed() -> None:
    client = AlwaysFailingTelegramApiClient()
    gateway = TelegramGateway(
        api_client=client,
        channel_id="channel",
        operator_auth=OperatorAuthService(
            allowed_operator_ids=frozenset(),
            operator_token=None,
        ),
    )
    queue = InMemoryPublicationQueue()
    service = PublicationService(publication_queue=queue, telegram_gateway=gateway)
    await service.enqueue_publication(candidate_id="c1", text="tweet body")
    for _ in range(3):
        await service.process_pending_publications()
    documents = await queue.find({"status": "failed"})
    assert len(documents) == 1
