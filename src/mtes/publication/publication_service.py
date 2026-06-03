"""Publication queue processing per Architecture §7.6 and SRS §8."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from mtes.shared.exceptions import TelegramGatewayUnavailableError
from mtes.telegram.telegram_gateway import TelegramGateway

DEFAULT_PUBLICATION_QUEUE_SIZE = 100
PUBLICATION_MAX_RETRIES = 3


class PublicationQueueRepository(Protocol):
    async def insert_one(self, document: dict[str, Any]) -> str:
        ...

    async def find(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        ...

    async def replace_one(self, document_id: str, document: dict[str, Any]) -> None:
        ...


@dataclass(frozen=True, slots=True)
class PublicationQueueItem:
    queue_id: str
    candidate_id: str
    text: str
    status: str
    scheduled_at: datetime | None
    retry_count: int


@dataclass
class PublicationService:
    """Enqueue and publish candidate texts via Telegram."""

    publication_queue: PublicationQueueRepository
    telegram_gateway: TelegramGateway
    max_queue_size: int = DEFAULT_PUBLICATION_QUEUE_SIZE

    async def enqueue_publication(
        self,
        *,
        candidate_id: str,
        text: str,
        scheduled_at: datetime | None = None,
    ) -> PublicationQueueItem:
        pending = await self.publication_queue.find({"status": "pending"})
        if len(pending) >= self.max_queue_size:
            raise RuntimeError("Publication queue is full")
        queue_id = str(uuid4())
        document = {
            "_id": queue_id,
            "queue_id": queue_id,
            "candidate_id": candidate_id,
            "text": text,
            "status": "pending",
            "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
            "retry_count": 0,
        }
        await self.publication_queue.insert_one(document)
        return PublicationQueueItem(
            queue_id=queue_id,
            candidate_id=candidate_id,
            text=text,
            status="pending",
            scheduled_at=scheduled_at,
            retry_count=0,
        )

    async def process_pending_publications(self, *, limit: int = 10) -> int:
        """Publish due queue items immediately or when scheduled time has passed."""
        now = datetime.now(UTC)
        pending = await self.publication_queue.find({"status": "pending"})
        published_count = 0
        for document in pending[:limit]:
            scheduled_raw = document.get("scheduled_at")
            if scheduled_raw is not None:
                scheduled_at = datetime.fromisoformat(str(scheduled_raw))
                if scheduled_at > now:
                    continue
            try:
                await self.telegram_gateway.publish_text(str(document["text"]))
            except TelegramGatewayUnavailableError:
                retry_count = int(document.get("retry_count", 0)) + 1
                document["retry_count"] = retry_count
                if retry_count >= PUBLICATION_MAX_RETRIES:
                    document["status"] = "failed"
                await self.publication_queue.replace_one(str(document["_id"]), document)
                continue
            document["status"] = "published"
            document["published_at"] = now.isoformat()
            await self.publication_queue.replace_one(str(document["_id"]), document)
            published_count += 1
        return published_count
