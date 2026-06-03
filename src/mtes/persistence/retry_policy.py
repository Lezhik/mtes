"""Infrastructure retry policy per SRS §13.1."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from mtes.shared.exceptions import MongoDbUnavailableError

T = TypeVar("T")

INFRASTRUCTURE_RETRY_DELAYS_SECONDS: tuple[float, ...] = (1.0, 2.0, 4.0)
INFRASTRUCTURE_MAX_ATTEMPTS: int = 3


async def with_infrastructure_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    error_factory: Callable[[Exception], Exception] | None = None,
) -> T:
    """Execute an async operation with 1s / 2s / 4s backoff, max 3 attempts."""
    last_error: Exception | None = None

    for attempt_index in range(INFRASTRUCTURE_MAX_ATTEMPTS):
        try:
            return await operation()
        except Exception as exc:  # noqa: BLE001 — infrastructure boundary
            last_error = exc
            if attempt_index >= INFRASTRUCTURE_MAX_ATTEMPTS - 1:
                break
            await asyncio.sleep(INFRASTRUCTURE_RETRY_DELAYS_SECONDS[attempt_index])

    if error_factory is not None and last_error is not None:
        raise error_factory(last_error) from last_error

    if last_error is not None:
        raise last_error

    raise MongoDbUnavailableError("Infrastructure retry failed without exception detail")
