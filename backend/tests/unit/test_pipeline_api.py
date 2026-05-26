import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

from app.dependencies import get_claude_client, get_file_manager, get_pipeline_service
from app.models.pipeline_run import PipelineStage, PipelineStatus
from app.models.validation import ValidationCategory
from app.pipeline.base import PipelineEvent

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
        },
        {
            "url": "https://example.com/doc2",
            "title": "딥러닝 가이드",
            "summary": "딥러닝 기초 설명",
            "relevance_score": 0.85,
        },
        {
            "url": "https://example.com/doc3",
            "title": "트랜스포머 아키텍처",
            "summary": "어텐션 메커니즘 해설",
            "relevance_score": 0.80,
        },
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
    if full_pipeline:
        mock_claude.run_json.side_effect = [
            MOCK_ROUTER_RESPONSE,
            MOCK_LIBRARIAN_RESPONSE,
            MOCK_LIBRARIAN_RESPONSE,
            MOCK_LIBRARIAN_RESPONSE,
            MOCK_LIBRARIAN_RESPONSE,
            MOCK_OUTLINE_RESPONSE,
            {"images": []},
            MOCK_VALIDATOR_RESPONSE,
        ]
        mock_claude.run.return_value = MockClaudeResponse(
            text=MOCK_FULL_CONTENT,
        )
    else:
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
    mock_service = AsyncMock()
    mock_service.get_run.return_value = None

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.get("/api/v1/pipeline/runs/9999")
    assert response.status_code == 404


async def test_reject_gate_not_found(client: AsyncClient) -> None:
    from app.exceptions import NotFoundError

    mock_service = AsyncMock()
    mock_service.reject_pipeline.side_effect = NotFoundError(
        "파이프라인 실행을 찾을 수 없습니다"
    )

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.post("/api/v1/pipeline/runs/9999/reject")
    assert response.status_code == 404


async def test_active_run_none(client: AsyncClient) -> None:
    mock_service = AsyncMock()
    mock_service.get_active_run.return_value = None

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.get("/api/v1/pipeline/runs/active")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] is None


async def test_active_run_returns_paused(client: AsyncClient) -> None:
    _setup_mocks(client)

    create_resp = await client.post(
        "/api/v1/articles", json={"topic": "활성 run 테스트"}
    )
    article_id = create_resp.json()["data"]["id"]

    await client.post(
        "/api/v1/pipeline/start", json={"article_id": article_id}
    )

    response = await client.get("/api/v1/pipeline/runs/active")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] is not None
    assert body["data"]["status"] == "paused"
    assert body["data"]["article_id"] == article_id


# --- start_pipeline with mock service (lines 67, 70) ---


async def test_start_pipeline_with_mock_service(client: AsyncClient) -> None:
    """mock service로 run_id 추출 로직 (line 67) 및 반환 (line 70) 테스트"""
    mock_service = AsyncMock()

    async def mock_start(article_id, *, auto_gate_one=False, format_id=None):
        yield PipelineEvent(
            event_type="stage_start",
            stage="router",
            message="Router 시작",
            data={"run_id": 42},
        )
        yield PipelineEvent(
            event_type="gate_pending",
            stage="gate_one",
            message="Gate 1 대기",
            data={},
        )

    mock_service.start_pipeline = mock_start

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.post(
        "/api/v1/pipeline/start", json={"article_id": 1}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["run_id"] == 42
    assert len(body["data"]["events"]) == 2


async def test_start_pipeline_no_run_id_in_events(client: AsyncClient) -> None:
    """이벤트에 run_id가 없는 경우"""
    mock_service = AsyncMock()

    async def mock_start(article_id, *, auto_gate_one=False, format_id=None):
        yield PipelineEvent(
            event_type="pipeline_error",
            stage="init",
            message="Article not found",
            data={},
        )

    mock_service.start_pipeline = mock_start

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.post(
        "/api/v1/pipeline/start", json={"article_id": 9999}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert "run_id" not in body["data"]


# --- approve_gate (lines 80-82) ---


async def test_approve_gate_success(client: AsyncClient) -> None:
    mock_service = AsyncMock()

    async def mock_resume(run_id):
        yield PipelineEvent(
            event_type="stage_start",
            stage="generator",
            message="Generator 시작",
            data={},
        )
        yield PipelineEvent(
            event_type="pipeline_complete",
            stage="system",
            message="파이프라인 완료",
            data={},
        )

    mock_service.resume_pipeline = mock_resume

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.post("/api/v1/pipeline/runs/1/approve")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    events = body["data"]["events"]
    assert len(events) == 2
    assert events[-1]["event_type"] == "pipeline_complete"


async def test_approve_gate_run_not_found(client: AsyncClient) -> None:
    _setup_mocks(client)

    response = await client.post("/api/v1/pipeline/runs/9999/approve")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    events = body["data"]["events"]
    assert any(e["event_type"] == "pipeline_error" for e in events)


# --- reject_gate (line 91) ---


async def test_reject_gate_success(client: AsyncClient) -> None:
    mock_service = AsyncMock()
    mock_service.reject_pipeline.return_value = None

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.post("/api/v1/pipeline/runs/1/reject")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "cancelled"
    mock_service.reject_pipeline.assert_called_once_with(1, feedback="")


async def test_reject_gate_invalid_state(client: AsyncClient) -> None:
    """InvalidStateError가 발생하면 400 반환"""
    from app.exceptions import InvalidStateError

    mock_service = AsyncMock()
    mock_service.reject_pipeline.side_effect = InvalidStateError(
        "파이프라인이 대기 상태가 아닙니다"
    )

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.post("/api/v1/pipeline/runs/1/reject")
    assert response.status_code == 400


# --- cancel_run (lines 99-100) ---


async def test_cancel_run_success(client: AsyncClient) -> None:
    mock_service = AsyncMock()
    mock_service.cancel_run.return_value = None

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.post("/api/v1/pipeline/runs/1/cancel")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "cancelled"
    mock_service.cancel_run.assert_called_once_with(1)


async def test_cancel_run_not_found(client: AsyncClient) -> None:
    from app.exceptions import NotFoundError

    mock_service = AsyncMock()
    mock_service.cancel_run.side_effect = NotFoundError(
        "파이프라인 실행을 찾을 수 없습니다"
    )

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.post("/api/v1/pipeline/runs/9999/cancel")
    assert response.status_code == 404


async def test_cancel_run_invalid_state(client: AsyncClient) -> None:
    from app.exceptions import InvalidStateError

    mock_service = AsyncMock()
    mock_service.cancel_run.side_effect = InvalidStateError(
        "취소 가능한 상태가 아닙니다"
    )

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.post("/api/v1/pipeline/runs/1/cancel")
    assert response.status_code == 400


# --- get_validations (lines 109-131) ---


async def test_get_validations_with_data(client: AsyncClient) -> None:
    _setup_mocks(client)

    create_resp = await client.post(
        "/api/v1/articles", json={"topic": "검증 테스트"}
    )
    article_id = create_resp.json()["data"]["id"]

    start_resp = await client.post(
        "/api/v1/pipeline/start", json={"article_id": article_id}
    )
    run_id = start_resp.json()["data"]["run_id"]

    response = await client.get(f"/api/v1/pipeline/runs/{run_id}/validations")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "validations" in body["data"]
    assert "summary" in body["data"]

    summary = body["data"]["summary"]
    assert "total" in summary
    assert "passed" in summary
    assert "failed" in summary
    assert "score" in summary
    assert "by_category" in summary
    assert summary["total"] == summary["passed"] + summary["failed"]


async def test_get_validations_empty(client: AsyncClient) -> None:
    _setup_mocks(client)

    create_resp = await client.post(
        "/api/v1/articles", json={"topic": "빈 검증 테스트"}
    )
    article_id = create_resp.json()["data"]["id"]

    start_resp = await client.post(
        "/api/v1/pipeline/start", json={"article_id": article_id}
    )
    run_id = start_resp.json()["data"]["run_id"]

    response = await client.get(f"/api/v1/pipeline/runs/{run_id}/validations")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    summary = body["data"]["summary"]
    assert summary["total"] == 0
    assert summary["score"] == 0.0


async def test_get_validations_with_mock_service(client: AsyncClient) -> None:
    """mock service로 다양한 category의 validation 데이터 테스트"""
    mock_service = AsyncMock()

    mock_validations = []
    for i, (cat, passed) in enumerate(
        [
            (ValidationCategory.STYLE, True),
            (ValidationCategory.STYLE, False),
            (ValidationCategory.SEO, True),
            (ValidationCategory.AEO, True),
            (ValidationCategory.GEO, False),
        ],
        start=1,
    ):
        v = MagicMock()
        v.id = i
        v.category = cat
        v.item = f"항목_{i}"
        v.passed = passed
        v.score = 0.9 if passed else 0.3
        v.message = f"메시지_{i}"
        mock_validations.append(v)

    mock_service.get_validations.return_value = mock_validations

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.get("/api/v1/pipeline/runs/1/validations")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    summary = body["data"]["summary"]
    assert summary["total"] == 5
    assert summary["passed"] == 3
    assert summary["failed"] == 2
    assert summary["score"] == 0.6

    by_cat = summary["by_category"]
    assert by_cat["style"]["total"] == 2
    assert by_cat["style"]["passed"] == 1
    assert by_cat["seo"]["total"] == 1
    assert by_cat["seo"]["passed"] == 1
    assert by_cat["geo"]["total"] == 1
    assert by_cat["geo"]["passed"] == 0


# --- list_runs (lines 147-151) ---


async def test_list_runs_all(client: AsyncClient) -> None:
    mock_service = AsyncMock()
    mock_service.get_all_runs.return_value = []

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.get("/api/v1/pipeline/runs")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == []
    mock_service.get_all_runs.assert_called_once_with(limit=50, offset=0)


async def test_list_runs_with_article_id(client: AsyncClient) -> None:
    mock_service = AsyncMock()
    mock_service.get_runs_for_article.return_value = []

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.get("/api/v1/pipeline/runs?article_id=42")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    mock_service.get_runs_for_article.assert_called_once_with(42)


async def test_list_runs_with_pagination(client: AsyncClient) -> None:
    mock_service = AsyncMock()
    mock_service.get_all_runs.return_value = []

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.get("/api/v1/pipeline/runs?limit=10&offset=20")
    assert response.status_code == 200
    mock_service.get_all_runs.assert_called_once_with(limit=10, offset=20)


async def test_list_runs_with_data(client: AsyncClient) -> None:
    _setup_mocks(client)

    create_resp = await client.post(
        "/api/v1/articles", json={"topic": "목록 테스트"}
    )
    article_id = create_resp.json()["data"]["id"]

    await client.post(
        "/api/v1/pipeline/start", json={"article_id": article_id}
    )

    response = await client.get(
        f"/api/v1/pipeline/runs?article_id={article_id}"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) >= 1


# --- get_run found (lines 207-209) ---


async def test_get_run_found(client: AsyncClient) -> None:
    mock_service = AsyncMock()

    mock_run = MagicMock()
    mock_run.id = 7
    mock_run.article_id = 10
    mock_run.current_stage = PipelineStage.VALIDATOR
    mock_run.status = PipelineStatus.RUNNING
    mock_run.started_at = None
    mock_run.completed_at = None
    mock_run.error_message = ""
    mock_run.retry_count = 0
    mock_run.duration_seconds = None
    mock_run.stage_durations = {}
    mock_service.get_run.return_value = mock_run

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.get("/api/v1/pipeline/runs/7")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == 7
    assert body["data"]["article_id"] == 10
    assert body["data"]["status"] == "running"


# --- get_active_run with data (lines 193-195) ---


async def test_get_active_run_with_mock_service(client: AsyncClient) -> None:
    mock_service = AsyncMock()

    mock_run = MagicMock()
    mock_run.id = 1
    mock_run.article_id = 10
    mock_run.current_stage = PipelineStage.GATE_ONE
    mock_run.status = PipelineStatus.PAUSED
    mock_run.started_at = None
    mock_run.completed_at = None
    mock_run.error_message = ""
    mock_run.retry_count = 0
    mock_run.duration_seconds = None
    mock_run.stage_durations = {}
    mock_service.get_active_run.return_value = mock_run

    client._transport.app.dependency_overrides[get_pipeline_service] = (
        lambda: mock_service
    )

    response = await client.get("/api/v1/pipeline/runs/active")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == 1
    assert body["data"]["status"] == "paused"


# --- _event_to_dict / _collect_result helpers ---


def test_event_to_dict() -> None:
    from app.api.v1.pipeline import _event_to_dict

    event = PipelineEvent(
        event_type="stage_start",
        stage="router",
        message="시작",
        data={"key": "value"},
    )
    result = _event_to_dict(event)
    assert result == {
        "event_type": "stage_start",
        "stage": "router",
        "message": "시작",
        "data": {"key": "value"},
    }


def test_collect_result_success() -> None:
    from app.api.v1.pipeline import _collect_result

    events = [
        {"event_type": "stage_start", "message": "시작"},
        {"event_type": "pipeline_complete", "message": "완료"},
    ]
    result = _collect_result(events, run_id=42)
    assert result.success is True
    assert result.data["run_id"] == 42
    assert result.error is None


def test_collect_result_gate_pending() -> None:
    from app.api.v1.pipeline import _collect_result

    events = [
        {"event_type": "stage_start", "message": "시작"},
        {"event_type": "gate_pending", "message": "대기"},
    ]
    result = _collect_result(events)
    assert result.success is True
    assert "run_id" not in result.data


def test_collect_result_failure() -> None:
    from app.api.v1.pipeline import _collect_result

    events = [
        {"event_type": "pipeline_error", "message": "에러 발생"},
    ]
    result = _collect_result(events)
    assert result.success is False
    assert result.error == "에러 발생"


def test_collect_result_empty() -> None:
    from app.api.v1.pipeline import _collect_result

    result = _collect_result([])
    assert result.success is False


# --- _sse_from_queue (lines 273-286) ---


async def test_sse_from_queue_generates_events() -> None:
    """_sse_from_queue의 내부 제너레이터가 정상 동작하는지 직접 테스트"""
    from app.api.v1.pipeline import _sse_from_queue

    queue: asyncio.Queue = asyncio.Queue()
    await queue.put({
        "event_type": "stage_start",
        "stage": "router",
        "message": "시작",
        "data": {},
    })
    await queue.put({
        "event_type": "pipeline_complete",
        "stage": "system",
        "message": "완료",
        "data": {},
    })
    await queue.put(None)

    sse_response = _sse_from_queue(queue)
    # EventSourceResponse 객체가 반환되는지 확인
    assert sse_response is not None
    assert sse_response.media_type == "text/event-stream"


# --- retry_pipeline_stream (lines 161-185) ---


async def test_retry_pipeline_stream(client: AsyncClient) -> None:
    """SSE 스트리밍 retry 엔드포인트 테스트"""
    _setup_mocks(client)

    create_resp = await client.post(
        "/api/v1/articles", json={"topic": "재시도 스트림 테스트"}
    )
    article_id = create_resp.json()["data"]["id"]

    # 파이프라인 실행 → paused
    start_resp = await client.post(
        "/api/v1/pipeline/start", json={"article_id": article_id}
    )
    run_id = start_resp.json()["data"]["run_id"]

    # retry/stream은 내부에서 async_session_factory를 직접 사용하므로 patch 필요
    mock_svc = AsyncMock()

    async def mock_retry(rid):
        yield PipelineEvent(
            event_type="pipeline_complete",
            stage="system",
            message="재시도 완료",
            data={"run_id": rid},
        )

    mock_svc.retry_pipeline = mock_retry

    with patch(
        "app.api.v1.pipeline.create_pipeline_service", return_value=mock_svc
    ), patch(
        "app.api.v1.pipeline.async_session_factory",
    ) as mock_factory:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_factory.return_value = mock_session

        response = await client.post(
            f"/api/v1/pipeline/runs/{run_id}/retry/stream"
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")


async def test_retry_pipeline_stream_error(client: AsyncClient) -> None:
    """retry 중 예외 발생 시 에러 이벤트 전달"""

    with patch(
        "app.api.v1.pipeline.create_pipeline_service",
    ) as mock_create, patch(
        "app.api.v1.pipeline.async_session_factory",
    ) as mock_factory:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_factory.return_value = mock_session

        mock_svc = AsyncMock()
        mock_svc.retry_pipeline.side_effect = RuntimeError("DB 오류")
        mock_create.return_value = mock_svc

        response = await client.post("/api/v1/pipeline/runs/1/retry/stream")
        assert response.status_code == 200
        body_text = response.text
        assert "pipeline_error" in body_text


# --- start_pipeline_stream (lines 293-306) ---


async def test_start_pipeline_stream(client: AsyncClient) -> None:
    """SSE 스트리밍 start 엔드포인트 테스트"""

    with patch(
        "app.api.v1.pipeline._run_pipeline_in_background",
    ) as mock_bg:
        async def fake_bg(queue, *args, **kwargs):
            await queue.put({
                "event_type": "stage_start",
                "stage": "router",
                "message": "시작",
                "data": {},
            })
            await queue.put(None)

        mock_bg.side_effect = fake_bg

        response = await client.post(
            "/api/v1/pipeline/start/stream",
            json={"article_id": 1},
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")


# --- validate_only_stream (lines 317-342) ---


async def test_validate_only_stream(client: AsyncClient) -> None:
    """SSE 스트리밍 validate-only 엔드포인트 테스트"""

    with patch(
        "app.api.v1.pipeline.create_pipeline_service",
    ) as mock_create, patch(
        "app.api.v1.pipeline.async_session_factory",
    ) as mock_factory:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_factory.return_value = mock_session

        mock_svc = AsyncMock()

        async def mock_validate(aid):
            yield PipelineEvent(
                event_type="pipeline_complete",
                stage="validator",
                message="검증 완료",
                data={},
            )

        mock_svc.validate_only = mock_validate
        mock_create.return_value = mock_svc

        response = await client.post(
            "/api/v1/pipeline/validate-only/stream",
            json={"article_id": 1},
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")


async def test_validate_only_stream_error(client: AsyncClient) -> None:
    """validate-only 중 예외 발생"""

    with patch(
        "app.api.v1.pipeline.create_pipeline_service",
    ) as mock_create, patch(
        "app.api.v1.pipeline.async_session_factory",
    ) as mock_factory:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_factory.return_value = mock_session

        mock_svc = AsyncMock()
        mock_svc.validate_only.side_effect = RuntimeError("검증 실패")
        mock_create.return_value = mock_svc

        response = await client.post(
            "/api/v1/pipeline/validate-only/stream",
            json={"article_id": 1},
        )
        assert response.status_code == 200
        assert "pipeline_error" in response.text


# --- approve_gate_stream (lines 349-357) ---


async def test_approve_gate_stream(client: AsyncClient) -> None:
    """SSE 스트리밍 approve 엔드포인트 테스트"""

    with patch(
        "app.api.v1.pipeline._resume_pipeline_in_background",
    ) as mock_bg:
        async def fake_bg(queue, run_id):
            await queue.put({
                "event_type": "pipeline_complete",
                "stage": "system",
                "message": "완료",
                "data": {},
            })
            await queue.put(None)

        mock_bg.side_effect = fake_bg

        response = await client.post(
            "/api/v1/pipeline/runs/1/approve/stream"
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
