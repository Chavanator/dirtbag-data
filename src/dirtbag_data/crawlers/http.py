"""Cliente HTTP asíncrono y cortés compartido por todos los adaptadores (spec §30).

- rate limiting configurable entre peticiones
- User-Agent identificable (DIRTBAG_HTTP_USER_AGENT)
- timeouts + reintentos con backoff ante errores de red/5xx
- los 4xx NO se reintentalan (un 404/403 es definitivo)
"""

from __future__ import annotations

import asyncio

import httpx

from dirtbag_data.config.loader import HttpConfig


class PoliteHttpError(RuntimeError):
    """Fallo definitivo tras agotar reintentos o respuesta 4xx."""


class PoliteClient:
    def __init__(
        self,
        *,
        timeout: float = 20.0,
        max_retries: int = 3,
        rate_limit_seconds: float = 1.5,
        user_agent: str = "DirtBagBot/0.1",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.max_retries = max_retries
        self.rate_limit_seconds = rate_limit_seconds
        self._last_request = 0.0
        self._client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": user_agent, "Accept-Language": "en"},
            transport=transport,
        )

    @classmethod
    def from_settings(
        cls, cfg: HttpConfig, transport: httpx.AsyncBaseTransport | None = None
    ) -> PoliteClient:
        return cls(
            timeout=cfg.timeout,
            max_retries=cfg.max_retries,
            rate_limit_seconds=cfg.rate_limit_seconds,
            user_agent=cfg.user_agent,
            transport=transport,
        )

    async def __aenter__(self) -> PoliteClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _throttle(self) -> None:
        now = asyncio.get_event_loop().time()
        wait = self._last_request + self.rate_limit_seconds - now
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_request = asyncio.get_event_loop().time()

    async def get_text(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            if attempt:
                backoff = min(self.rate_limit_seconds * (2 ** (attempt - 1)), 30.0)
                if backoff > 0:
                    await asyncio.sleep(backoff)
            await self._throttle()
            try:
                response = await self._client.get(url)
            except httpx.TransportError as exc:  # red / timeout → reintentar
                last_error = exc
                continue
            if response.status_code >= 500:  # servidor caído → reintentar
                last_error = PoliteHttpError(f"HTTP {response.status_code} for {url}")
                continue
            if response.status_code >= 400:  # 4xx → definitivo, sin reintento
                raise PoliteHttpError(f"HTTP {response.status_code} for {url}")
            return response.text
        raise PoliteHttpError(f"giving up on {url} after {self.max_retries + 1} attempts: {last_error}")
