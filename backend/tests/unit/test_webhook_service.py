from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.webhook_service import dispatch_webhook


@pytest.mark.asyncio
async def test_dispatch_no_webhooks() -> None:
    with patch("app.services.webhook_service._load_webhooks", return_value=[]):
        await dispatch_webhook("pipeline_complete", {"run_id": 1})


@pytest.mark.asyncio
async def test_dispatch_no_matching_events() -> None:
    hooks = [{"url": "https://a.com", "events": ["gate_pending"], "active": True}]
    with patch("app.services.webhook_service._load_webhooks", return_value=hooks):
        await dispatch_webhook("pipeline_complete", {"run_id": 1})


@pytest.mark.asyncio
async def test_dispatch_inactive_webhook_skipped() -> None:
    hooks = [
        {"url": "https://a.com", "events": ["pipeline_complete"], "active": False}
    ]
    with patch("app.services.webhook_service._load_webhooks", return_value=hooks):
        await dispatch_webhook("pipeline_complete", {"run_id": 1})


@pytest.mark.asyncio
async def test_dispatch_sends_to_matching_webhook() -> None:
    hooks = [
        {
            "url": "https://a.com/hook",
            "events": ["pipeline_complete"],
            "active": True,
            "name": "test-hook",
        }
    ]

    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.services.webhook_service._load_webhooks", return_value=hooks),
        patch("app.services.webhook_service.httpx.AsyncClient", return_value=mock_client),
    ):
        await dispatch_webhook("pipeline_complete", {"run_id": 1})

    mock_client.post.assert_awaited_once()
    call_args = mock_client.post.call_args
    assert call_args[0][0] == "https://a.com/hook"
    body = call_args[1]["json"]
    assert body["event"] == "pipeline_complete"
    assert body["data"]["run_id"] == 1


@pytest.mark.asyncio
async def test_dispatch_handles_http_error_gracefully() -> None:
    hooks = [
        {
            "url": "https://a.com/hook",
            "events": ["pipeline_error"],
            "active": True,
            "name": "fail-hook",
        }
    ]

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.services.webhook_service._load_webhooks", return_value=hooks),
        patch("app.services.webhook_service.httpx.AsyncClient", return_value=mock_client),
    ):
        await dispatch_webhook("pipeline_error", {"run_id": 1, "error": "timeout"})


def test_load_webhooks_from_file() -> None:
    from app.services.webhook_service import _load_webhooks

    data = [{"url": "https://a.com", "events": [], "active": True}]
    with patch("app.services.webhook_service.WEBHOOKS_FILE") as mock_file:
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = json.dumps(data)
        result = _load_webhooks()

    assert result == data


def test_load_webhooks_no_file() -> None:
    from app.services.webhook_service import _load_webhooks

    with patch("app.services.webhook_service.WEBHOOKS_FILE") as mock_file:
        mock_file.exists.return_value = False
        result = _load_webhooks()

    assert result == []
