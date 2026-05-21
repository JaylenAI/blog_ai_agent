import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import Response

from app.api.middleware.rate_limiter import RateLimiterMiddleware


def _make_request(
    ip: str = "127.0.0.1",
    forwarded_for: str | None = None,
) -> MagicMock:
    request = MagicMock(spec=Request)
    request.client = MagicMock()
    request.client.host = ip
    if forwarded_for:
        request.headers = {"x-forwarded-for": forwarded_for}
    else:
        request.headers = {}
    return request


def test_get_client_ip_direct() -> None:
    middleware = RateLimiterMiddleware(MagicMock(), limit=10, window=60)
    request = _make_request(ip="192.168.1.1")
    assert middleware._get_client_ip(request) == "192.168.1.1"


def test_get_client_ip_forwarded() -> None:
    middleware = RateLimiterMiddleware(MagicMock(), limit=10, window=60)
    request = _make_request(forwarded_for="10.0.0.1, 10.0.0.2")
    assert middleware._get_client_ip(request) == "10.0.0.1"


def test_get_client_ip_no_client() -> None:
    middleware = RateLimiterMiddleware(MagicMock(), limit=10, window=60)
    request = MagicMock(spec=Request)
    request.client = None
    request.headers = {}
    assert middleware._get_client_ip(request) == "unknown"


def test_cleanup_removes_expired() -> None:
    middleware = RateLimiterMiddleware(MagicMock(), limit=10, window=60)
    now = time.monotonic()
    middleware._requests["test"] = [now - 100, now - 70, now - 10, now - 5]
    middleware._cleanup("test", now)
    assert len(middleware._requests["test"]) == 2


@pytest.mark.asyncio
async def test_allows_requests_under_limit() -> None:
    middleware = RateLimiterMiddleware(MagicMock(), limit=3, window=60)
    expected_response = Response(status_code=200)
    call_next = AsyncMock(return_value=expected_response)
    request = _make_request()

    for _ in range(3):
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_blocks_requests_over_limit() -> None:
    middleware = RateLimiterMiddleware(MagicMock(), limit=2, window=60)
    expected_response = Response(status_code=200)
    call_next = AsyncMock(return_value=expected_response)
    request = _make_request()

    await middleware.dispatch(request, call_next)
    await middleware.dispatch(request, call_next)
    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 429


@pytest.mark.asyncio
async def test_different_ips_have_separate_limits() -> None:
    middleware = RateLimiterMiddleware(MagicMock(), limit=1, window=60)
    expected_response = Response(status_code=200)
    call_next = AsyncMock(return_value=expected_response)

    req1 = _make_request(ip="10.0.0.1")
    req2 = _make_request(ip="10.0.0.2")

    resp1 = await middleware.dispatch(req1, call_next)
    resp2 = await middleware.dispatch(req2, call_next)

    assert resp1.status_code == 200
    assert resp2.status_code == 200

    resp3 = await middleware.dispatch(req1, call_next)
    assert resp3.status_code == 429
