"""Tests del cliente cortés — sin red (httpx.MockTransport)."""

import httpx
import pytest

from dirtbag_data.crawlers.http import PoliteClient, PoliteHttpError


def _client(handler, retries: int = 3) -> PoliteClient:
    return PoliteClient(
        timeout=5.0,
        max_retries=retries,
        rate_limit_seconds=0.0,
        user_agent="DirtBagBot/0.1 (test)",
        transport=httpx.MockTransport(handler),
    )


async def test_get_text_success():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers["user-agent"])
        return httpx.Response(200, text="hola")

    client = _client(handler)
    try:
        assert await client.get_text("https://example.test/x") == "hola"
        assert seen == ["DirtBagBot/0.1 (test)"]
    finally:
        await client.aclose()


async def test_4xx_fails_fast_without_retry():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(404)

    client = _client(handler)
    try:
        with pytest.raises(PoliteHttpError, match="HTTP 404"):
            await client.get_text("https://example.test/gone")
        assert calls["n"] == 1  # sin reintentos ante 4xx
    finally:
        await client.aclose()


async def test_5xx_retries_then_succeeds():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, text="ok")

    client = _client(handler)
    try:
        assert await client.get_text("https://example.test/flaky") == "ok"
        assert calls["n"] == 3
    finally:
        await client.aclose()


async def test_transport_error_retries_then_gives_up():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        raise httpx.ConnectError("boom", request=request)

    client = _client(handler, retries=2)
    try:
        with pytest.raises(PoliteHttpError, match="giving up"):
            await client.get_text("https://example.test/down")
        assert calls["n"] == 3  # intento inicial + 2 reintentos
    finally:
        await client.aclose()
