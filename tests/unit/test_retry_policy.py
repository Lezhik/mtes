"""Unit tests for infrastructure retry policy."""

import pytest

from mtes.persistence.retry_policy import (
    INFRASTRUCTURE_MAX_ATTEMPTS,
    with_infrastructure_retry,
)


@pytest.mark.asyncio
async def test_retry_succeeds_on_second_attempt() -> None:
    attempts = 0

    async def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ConnectionError("temporary")
        return "ok"

    result = await with_infrastructure_retry(flaky)
    assert result == "ok"
    assert attempts == 2


@pytest.mark.asyncio
async def test_retry_raises_after_max_attempts() -> None:
    async def always_fail() -> None:
        raise ConnectionError("persistent")

    with pytest.raises(ConnectionError):
        await with_infrastructure_retry(always_fail)

    assert INFRASTRUCTURE_MAX_ATTEMPTS == 3
