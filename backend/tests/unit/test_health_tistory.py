from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient


async def test_health_detailed_tistory_ok(client: AsyncClient) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_resp)
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.api.v1.health.settings") as mock_settings,
        patch("app.api.v1.health.httpx.AsyncClient", return_value=mock_http),
    ):
        mock_settings.tistory_blog_url = "https://test.tistory.com"
        mock_settings.claude_code_path = "claude"
        mock_settings.obsidian_vault_path = ""
        mock_settings.log_level = "INFO"

        response = await client.get("/api/v1/health/detailed")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    checks = body["data"]["checks"]
    assert "tistory" in checks
    assert checks["tistory"]["status"] == "ok"
    assert checks["tistory"]["http_status"] == 200


async def test_health_detailed_tistory_error(client: AsyncClient) -> None:
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(side_effect=Exception("Connection refused"))
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.api.v1.health.settings") as mock_settings,
        patch("app.api.v1.health.httpx.AsyncClient", return_value=mock_http),
    ):
        mock_settings.tistory_blog_url = "https://test.tistory.com"
        mock_settings.claude_code_path = "claude"
        mock_settings.obsidian_vault_path = ""
        mock_settings.log_level = "INFO"

        response = await client.get("/api/v1/health/detailed")

    body = response.json()
    checks = body["data"]["checks"]
    assert checks["tistory"]["status"] == "error"


async def test_health_detailed_tistory_disabled(client: AsyncClient) -> None:
    with patch("app.api.v1.health.settings") as mock_settings:
        mock_settings.tistory_blog_url = ""
        mock_settings.claude_code_path = "claude"
        mock_settings.obsidian_vault_path = ""
        mock_settings.log_level = "INFO"

        response = await client.get("/api/v1/health/detailed")

    body = response.json()
    checks = body["data"]["checks"]
    assert checks["tistory"]["status"] == "disabled"
