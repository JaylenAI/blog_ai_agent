from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "healthy"
    assert "version" in body["data"]
    assert "timestamp" in body["data"]


async def test_health_detailed_claude_ok(client: AsyncClient) -> None:
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"1.0.0", b"")

    with (
        patch("shutil.which", return_value="/usr/bin/claude"),
        patch("asyncio.create_subprocess_exec", return_value=mock_proc),
    ):
        response = await client.get("/api/v1/health/detailed")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["checks"]["claude_cli"]["status"] == "ok"
    assert body["data"]["checks"]["claude_cli"]["version"] == "1.0.0"


async def test_health_detailed_claude_missing(client: AsyncClient) -> None:
    with patch("shutil.which", return_value=None):
        response = await client.get("/api/v1/health/detailed")

    body = response.json()
    assert body["data"]["checks"]["claude_cli"]["status"] == "error"
    assert body["data"]["status"] == "degraded"


async def test_health_detailed_claude_timeout(client: AsyncClient) -> None:
    async def slow_communicate():
        raise TimeoutError("too slow")

    mock_proc = AsyncMock()
    mock_proc.communicate.side_effect = slow_communicate

    with (
        patch("shutil.which", return_value="/usr/bin/claude"),
        patch("asyncio.create_subprocess_exec", return_value=mock_proc),
        patch("asyncio.wait_for", side_effect=TimeoutError),
    ):
        response = await client.get("/api/v1/health/detailed")

    body = response.json()
    assert body["data"]["checks"]["claude_cli"]["status"] == "error"
