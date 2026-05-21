from dataclasses import dataclass
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

MOCK_LIBRARIAN_RESPONSE = {
    "references": [
        {
            "url": "https://example.com/doc1",
            "title": "AI 공식 문서",
            "summary": "AI 핵심 개념 요약",
            "relevance_score": 0.9,
        }
    ]
}

MOCK_OUTLINE_RESPONSE = {
    "outline": [
        {
            "section_number": 1,
            "heading": "1. 들어가며",
            "key_points": ["AI 정의"],
            "estimated_words": 500,
        },
    ],
    "total_sections": 1,
    "estimated_total_words": 500,
    "approach": "설명형",
}

MOCK_VALIDATOR_RESPONSE = {
    "validations": [
        {
            "category": "style",
            "item": "격식체 사용",
            "passed": True,
            "score": 0.9,
            "message": "격식체 확인됨",
        }
    ]
}

MOCK_FULL_CONTENT = (
    "# AI란 무엇인가?\n\n"
    + "## 1. 들어가며\n\n" + "가" * 500 + "\n\n"
    + "## 2. 개념\n\n" + "나" * 800 + "\n\n"
    + "## 3. 활용\n\n" + "다" * 800 + "\n\n"
    + "## 4. 기술\n\n" + "라" * 800 + "\n\n"
    + "## 5. 방법\n\n" + "마" * 800 + "\n\n"
    + "## 6. 주의\n\n" + "바" * 800 + "\n\n"
    + "## 7. 전망\n\n" + "사" * 800 + "\n\n"
    + "## 8. 마치며\n\n" + "아" * 500
)


@dataclass(frozen=True)
class MockClaudeResponse:
    text: str
    session_id: str = ""
    cost_usd: float = 0.0


def _setup_mocks(
    client: AsyncClient, *, full_pipeline: bool = False
) -> tuple[AsyncMock, MagicMock]:
    mock_claude = AsyncMock()
    mock_claude.run_json.side_effect = [
        MOCK_ROUTER_RESPONSE,
        MOCK_LIBRARIAN_RESPONSE,
        MOCK_LIBRARIAN_RESPONSE,
        MOCK_LIBRARIAN_RESPONSE,
        MOCK_LIBRARIAN_RESPONSE,
        MOCK_OUTLINE_RESPONSE,
        MOCK_VALIDATOR_RESPONSE,
    ]

    mock_fm = MagicMock()

    if full_pipeline:
        mock_claude.run.return_value = MockClaudeResponse(
            text=MOCK_FULL_CONTENT,
        )

        def read_json_effect(slug: str, filename: str) -> dict | list | None:
            if filename == "meta.json":
                return MOCK_ROUTER_RESPONSE
            if filename == "outline.json":
                return MOCK_OUTLINE_RESPONSE
            if filename == "references.json":
                return MOCK_LIBRARIAN_RESPONSE["references"]
            return None

        def read_text_effect(slug: str, filename: str) -> str | None:
            if filename == "final.md":
                return MOCK_FULL_CONTENT
            return None

        mock_fm.read_json.side_effect = read_json_effect
        mock_fm.read_text.side_effect = read_text_effect
    else:
        mock_fm.read_json.return_value = None

    client._transport.app.dependency_overrides[get_claude_client] = lambda: mock_claude
    client._transport.app.dependency_overrides[get_file_manager] = lambda: mock_fm
    return mock_claude, mock_fm


async def test_start_pipeline_pauses_at_gate(client: AsyncClient) -> None:
    _setup_mocks(client)

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
    assert "gate_pending" in event_types
    assert "pipeline_complete" not in event_types


async def test_start_pipeline_auto_gate(client: AsyncClient) -> None:
    _setup_mocks(client, full_pipeline=True)

    create_resp = await client.post(
        "/api/v1/articles", json={"topic": "AI란 무엇인가?"}
    )
    article_id = create_resp.json()["data"]["id"]

    response = await client.post(
        "/api/v1/pipeline/start",
        json={"article_id": article_id, "auto_gate_one": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    events = body["data"]["events"]
    event_types = [e["event_type"] for e in events]
    assert "gate_pending" in event_types


async def test_start_pipeline_returns_run_id(client: AsyncClient) -> None:
    _setup_mocks(client)

    create_resp = await client.post(
        "/api/v1/articles", json={"topic": "run_id 테스트"}
    )
    article_id = create_resp.json()["data"]["id"]

    response = await client.post(
        "/api/v1/pipeline/start", json={"article_id": article_id}
    )
    body = response.json()
    assert body["success"] is True
    assert "run_id" in body["data"]
    assert isinstance(body["data"]["run_id"], int)
    assert body["data"]["run_id"] > 0


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


async def test_reject_gate_not_found(client: AsyncClient) -> None:
    mock_claude = AsyncMock()
    mock_fm = MagicMock()

    client._transport.app.dependency_overrides[get_claude_client] = lambda: mock_claude
    client._transport.app.dependency_overrides[get_file_manager] = lambda: mock_fm

    response = await client.post("/api/v1/pipeline/runs/9999/reject")
    assert response.status_code == 400
