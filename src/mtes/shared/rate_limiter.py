"""Coroutine-safe global rate limiter per Architecture §7.10."""

import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class ProviderRateLimiter:
    """Token-bucket style limiter for a single provider."""

    max_requests_per_second: float
    _tokens: float = field(init=False)
    _last_refill: float = field(init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def __post_init__(self) -> None:
        self._tokens = self.max_requests_per_second
        self._last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._last_refill = now
        self._tokens = min(
            self.max_requests_per_second,
            self._tokens + elapsed * self.max_requests_per_second,
        )

    async def acquire(self) -> None:
        """Wait until a request token is available."""
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                deficit = 1.0 - self._tokens
                wait_seconds = deficit / self.max_requests_per_second
            await asyncio.sleep(wait_seconds)


class GlobalRateLimiter:
    """Shared rate-limit state keyed by provider name."""

    def __init__(self) -> None:
        self._limiters: dict[str, ProviderRateLimiter] = {}
        self._registry_lock = asyncio.Lock()

    async def register_provider(
        self,
        provider_name: str,
        *,
        max_requests_per_second: float,
    ) -> None:
        async with self._registry_lock:
            self._limiters[provider_name] = ProviderRateLimiter(
                max_requests_per_second=max_requests_per_second
            )

    async def acquire(self, provider_name: str) -> None:
        async with self._registry_lock:
            limiter = self._limiters.get(provider_name)
        if limiter is None:
            raise KeyError(f"Rate limiter not registered for provider: {provider_name}")
        await limiter.acquire()
