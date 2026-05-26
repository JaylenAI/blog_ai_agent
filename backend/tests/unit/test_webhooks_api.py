from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from httpx import AsyncClient


async def test_list_webhooks_empty(client: AsyncClient) -> None:
    with patch("app.api.v1.webhooks._load_webhooks", return_value=[]):
        response = await client.get("/api/v1/webhooks")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == []


async def test_list_webhooks_with_items(client: AsyncClient) -> None:
    hooks = [
        {
            "url": "https://example.com/hook1",
            "events": ["pipeline_complete"],
            "name": "hook-1",
            "active": True,
        }
    ]
    with patch("app.api.v1.webhooks._load_webhooks", return_value=hooks):
        response = await client.get("/api/v1/webhooks")

    body = response.json()
    assert len(body["data"]) == 1
    assert body["data"][0]["id"] == 0
    assert body["data"][0]["name"] == "hook-1"


async def test_create_webhook(client: AsyncClient) -> None:
    with (
        patch("app.api.v1.webhooks._load_webhooks", return_value=[]),
        patch("app.api.v1.webhooks._save_webhooks") as mock_save,
    ):
        response = await client.post(
            "/api/v1/webhooks",
            json={
                "url": "https://example.com/new",
                "events": ["pipeline_complete", "gate_pending"],
                "name": "new-hook",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "new-hook"
    assert body["data"]["active"] is True
    mock_save.assert_called_once()


async def test_create_webhook_auto_name(client: AsyncClient) -> None:
    existing = [{"url": "https://a.com", "events": [], "name": "h", "active": True}]
    with (
        patch("app.api.v1.webhooks._load_webhooks", return_value=existing),
        patch("app.api.v1.webhooks._save_webhooks"),
    ):
        response = await client.post(
            "/api/v1/webhooks",
            json={"url": "https://example.com/auto"},
        )

    body = response.json()
    assert body["data"]["name"] == "webhook-1"


async def test_delete_webhook_success(client: AsyncClient) -> None:
    hooks = [
        {"url": "https://a.com", "events": [], "name": "to-delete", "active": True}
    ]
    with (
        patch("app.api.v1.webhooks._load_webhooks", return_value=hooks),
        patch("app.api.v1.webhooks._save_webhooks") as mock_save,
    ):
        response = await client.delete("/api/v1/webhooks/0")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["removed"] == "to-delete"
    mock_save.assert_called_once()


async def test_delete_webhook_not_found(client: AsyncClient) -> None:
    with patch("app.api.v1.webhooks._load_webhooks", return_value=[]):
        response = await client.delete("/api/v1/webhooks/0")

    body = response.json()
    assert body["success"] is False


async def test_toggle_webhook(client: AsyncClient) -> None:
    hooks = [
        {"url": "https://a.com", "events": [], "name": "toggle-me", "active": True}
    ]
    with (
        patch("app.api.v1.webhooks._load_webhooks", return_value=hooks),
        patch("app.api.v1.webhooks._save_webhooks") as mock_save,
    ):
        response = await client.patch("/api/v1/webhooks/0/toggle")

    body = response.json()
    assert body["success"] is True
    assert body["data"]["active"] is False
    mock_save.assert_called_once()


async def test_toggle_webhook_not_found(client: AsyncClient) -> None:
    with patch("app.api.v1.webhooks._load_webhooks", return_value=[]):
        response = await client.patch("/api/v1/webhooks/5/toggle")

    body = response.json()
    assert body["success"] is False


def test_load_webhooks_file_exists() -> None:
    from app.api.v1.webhooks import _load_webhooks

    data = [{"url": "https://a.com", "events": [], "name": "h", "active": True}]
    with patch("app.api.v1.webhooks.WEBHOOKS_FILE") as mock_file:
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = json.dumps(data)
        result = _load_webhooks()

    assert result == data


def test_load_webhooks_no_file() -> None:
    from app.api.v1.webhooks import _load_webhooks

    with patch("app.api.v1.webhooks.WEBHOOKS_FILE") as mock_file:
        mock_file.exists.return_value = False
        result = _load_webhooks()

    assert result == []


def test_save_webhooks() -> None:
    from app.api.v1.webhooks import _save_webhooks

    data = [{"url": "https://a.com"}]
    with patch("app.api.v1.webhooks.WEBHOOKS_FILE") as mock_file:
        mock_parent = MagicMock()
        mock_file.parent = mock_parent
        _save_webhooks(data)

    mock_parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_file.write_text.assert_called_once()
