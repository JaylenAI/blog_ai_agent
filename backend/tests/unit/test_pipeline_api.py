from unittest.mock import AsyncMock, MagicMock

from httpx import AsyncClient

from app.dependencies import get_claude_client, get_file_manager

MOCK_ROUTER_RESPONSE = {
    "slug": "what-is-ai",
    "title": "AI란 무엇인가?",
    "category": "AI/ML",
    "target_audience": "beginner",
    "search_queries": ["AI definition"],
    "seo_keywords": ["AI", "인공지능"],
    "estimated_sections": 7,
}


async def test_start_pipeline_success(client: AsyncClient) -> None:
    mock_claude = AsyncMock()
    mock_claude.run_json.return_value = MOCK_ROUTER_RESPONSE
    mock_fm = MagicMock()

    client._transport.app.dependency_overrides[get_claude_client] = lambda: mock_claude
    client._transport.app.dependency_overrides[get_file_manager] = lambda: mock_fm

    create_resp = await client.post(
        "/api/v1/articles", json={"topic": "AI란 무엇인가?"}
    )
    article_id = create_resp.json()["data"]["id"]

    response = await client.post(
        "/api/v1/pipeline/start", json={"article_id": article_id}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    events = body["data"]["events"]
    event_types = [e["event_type"] for e in events]
    assert "stage_start" in event_types
    assert "stage_complete" in event_types
    assert "pipeline_complete" in event_types


async def test_start_pipeline_article_not_found(client: AsyncClient) -> None:
    mock_claude = AsyncMock()
    mock_fm = MagicMock()

    client._transport.app.dependency_overrides[get_claude_client] = lambda: mock_claude
    client._transport.app.dependency_overrides[get_file_manager] = lambda: mock_fm

    response = await client.post(
        "/api/v1/pipeline/start", json={"article_id": 9999}
    )

    body = response.json()
    assert body["success"] is False


async def test_start_pipeline_claude_failure(client: AsyncClient) -> None:
    mock_claude = AsyncMock()
    mock_claude.run_json.side_effect = RuntimeError("CLI not found")
    mock_fm = MagicMock()

    client._transport.app.dependency_overrides[get_claude_client] = lambda: mock_claude
    client._transport.app.dependency_overrides[get_file_manager] = lambda: mock_fm

    create_resp = await client.post(
        "/api/v1/articles", json={"topic": "실패 테스트"}
    )
    article_id = create_resp.json()["data"]["id"]

    response = await client.post(
        "/api/v1/pipeline/start", json={"article_id": article_id}
    )

    body = response.json()
    assert body["success"] is False

    events = body["data"]["events"]
    assert any(e["event_type"] == "stage_error" for e in events)


async def test_get_run_not_found(client: AsyncClient) -> None:
    mock_claude = AsyncMock()
    mock_fm = MagicMock()

    client._transport.app.dependency_overrides[get_claude_client] = lambda: mock_claude
    client._transport.app.dependency_overrides[get_file_manager] = lambda: mock_fm

    response = await client.get("/api/v1/pipeline/runs/9999")
    assert response.status_code == 404
