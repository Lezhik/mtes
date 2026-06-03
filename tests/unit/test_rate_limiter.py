"""Unit tests for global rate limiter."""

import asyncio
import time

import pytest

from mtes.shared.rate_limiter import GlobalRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_caps_request_rate() -> None:
    limiter = GlobalRateLimiter()
    await limiter.register_provider("telegram", max_requests_per_second=5.0)

    start = time.monotonic()
    for _ in range(3):
        await limiter.acquire("telegram")
    elapsed = time.monotonic() - start
    assert elapsed < 1.0


@pytest.mark.asyncio
async def test_unregistered_provider_raises_key_error() -> None:
    limiter = GlobalRateLimiter()
    with pytest.raises(KeyError):
        await limiter.acquire("unknown")


@pytest.mark.asyncio
async def test_concurrent_acquire_is_safe() -> None:
    limiter = GlobalRateLimiter()
    await limiter.register_provider("llm", max_requests_per_second=100.0)
    await asyncio.gather(*[limiter.acquire("llm") for _ in range(20)])
