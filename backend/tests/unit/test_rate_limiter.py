import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.middleware.rate_limiter import RateLimiterMiddleware


def _make_scope(
    ip: str = "127.0.0.1",
    forwarded_for: str | None = None,
    path: str = "/api/v1/test",
) -> dict:
    headers: list[tuple[bytes, bytes]] = []
    if forwarded_for:
        headers.append((b"x-forwarded-for", forwarded_for.encode()))
    return {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": headers,
        "client": (ip, 0),
    }


def test_get_client_ip_direct() -> None:
    middleware = RateLimiterMiddleware(MagicMock(), limit=10, window=60)
    scope = _make_scope(ip="192.168.1.1")
    assert middleware._get_client_ip(scope) == "192.168.1.1"


def test_get_client_ip_forwarded() -> None:
    middleware = RateLimiterMiddleware(MagicMock(), limit=10, window=60)
    scope = _make_scope(forwarded_for="10.0.0.1, 10.0.0.2")
    assert middleware._get_client_ip(scope) == "10.0.0.1"


def test_get_client_ip_no_client() -> None:
    middleware = RateLimiterMiddleware(MagicMock(), limit=10, window=60)
    scope = {"type": "http", "headers": [], "client": None}
    assert middleware._get_client_ip(scope) == "unknown"


def test_cleanup_removes_expired() -> None:
    middleware = RateLimiterMiddleware(MagicMock(), limit=10, window=60)
    now = time.monotonic()
    middleware._requests["test"] = [now - 100, now - 70, now - 10, now - 5]
    middleware._cleanup("test", now)
    assert len(middleware._requests["test"]) == 2


@pytest.mark.asyncio
async def test_allows_requests_under_limit() -> None:
    inner_app = AsyncMock()
    middleware = RateLimiterMiddleware(inner_app, limit=3, window=60)
    receive = AsyncMock()
    send = AsyncMock()

    for _ in range(3):
        scope = _make_scope()
        await middleware(scope, receive, send)

    assert inner_app.call_count == 3


@pytest.mark.asyncio
async def test_blocks_requests_over_limit() -> None:
    inner_app = AsyncMock()
    middleware = RateLimiterMiddleware(inner_app, limit=2, window=60)
    receive = AsyncMock()

    responses: list[dict] = []

    async def capture_send(message: dict) -> None:
        responses.append(message)

    for _ in range(2):
        await middleware(_make_scope(), receive, AsyncMock())

    responses.clear()
    await middleware(_make_scope(), receive, capture_send)

    status_msg = next(
        (m for m in responses if m["type"] == "http.response.start"), None
    )
    assert status_msg is not None
    assert status_msg["status"] == 429


@pytest.mark.asyncio
async def test_health_path_is_exempt() -> None:
    """health 엔드포인트는 제한을 초과해도 항상 통과한다."""
    inner_app = AsyncMock()
    middleware = RateLimiterMiddleware(inner_app, limit=1, window=60)
    receive = AsyncMock()

    # limit=1을 한참 넘겨도 health는 모두 inner_app으로 전달돼야 한다.
    for _ in range(5):
        await middleware(
            _make_scope(path="/api/v1/health"), receive, AsyncMock()
        )

    assert inner_app.call_count == 5


@pytest.mark.asyncio
async def test_health_detailed_path_is_exempt() -> None:
    inner_app = AsyncMock()
    middleware = RateLimiterMiddleware(inner_app, limit=1, window=60)
    receive = AsyncMock()

    for _ in range(5):
        await middleware(
            _make_scope(path="/api/v1/health/detailed"), receive, AsyncMock()
        )

    assert inner_app.call_count == 5


@pytest.mark.asyncio
async def test_different_ips_have_separate_limits() -> None:
    inner_app = AsyncMock()
    middleware = RateLimiterMiddleware(inner_app, limit=1, window=60)
    receive = AsyncMock()

    await middleware(_make_scope(ip="10.0.0.1"), receive, AsyncMock())
    await middleware(_make_scope(ip="10.0.0.2"), receive, AsyncMock())

    assert inner_app.call_count == 2

    responses: list[dict] = []

    async def capture_send(message: dict) -> None:
        responses.append(message)

    await middleware(_make_scope(ip="10.0.0.1"), receive, capture_send)

    status_msg = next(
        (m for m in responses if m["type"] == "http.response.start"), None
    )
    assert status_msg is not None
    assert status_msg["status"] == 429
