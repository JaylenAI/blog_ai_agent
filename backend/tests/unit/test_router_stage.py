from unittest.mock import AsyncMock, MagicMock

from app.pipeline.base import StageInput
from app.pipeline.stages.s1_router import RouterStage

MOCK_ROUTER_RESPONSE = {
    "slug": "what-is-ai",
    "title": "AI란 무엇인가? — 2026년 개발자 필수 가이드",
    "category": "AI/ML",
    "target_audience": "beginner",
    "search_queries": [
        "AI definition 2026",
        "artificial intelligence basics",
        "AI vs ML vs DL",
        "AI use cases developers",
    ],
    "seo_keywords": ["AI", "인공지능", "머신러닝", "딥러닝", "LLM"],
    "estimated_sections": 7,
}


def _make_stage(
    response: dict | None = None, error: Exception | None = None
) -> tuple[RouterStage, AsyncMock, MagicMock]:
    mock_claude = AsyncMock()
    if error:
        mock_claude.run_json.side_effect = error
    else:
        mock_claude.run_json.return_value = response or MOCK_ROUTER_RESPONSE

    mock_fm = MagicMock()
    return RouterStage(mock_claude, mock_fm), mock_claude, mock_fm


def _make_input() -> StageInput:
    return StageInput(article_id=1, slug="ai란-무엇인가", topic="AI란 무엇인가?")


async def test_router_success() -> None:
    stage, mock_claude, mock_fm = _make_stage()
    result = await stage.execute(_make_input())

    assert result.success is True
    assert result.data["slug"] == "what-is-ai"
    assert result.data["title"] == "AI란 무엇인가? — 2026년 개발자 필수 가이드"
    assert len(result.data["search_queries"]) == 4

    mock_claude.run_json.assert_called_once()
    mock_fm.write_json.assert_called_once_with(
        "ai란-무엇인가", "meta.json", mock_fm.write_json.call_args[0][2]
    )


async def test_router_name() -> None:
    stage, _, _ = _make_stage()
    assert stage.name == "router"


async def test_router_missing_fields() -> None:
    stage, _, _ = _make_stage(response={"slug": "test"})
    result = await stage.execute(_make_input())

    assert result.success is False
    assert "필수 필드 누락" in result.error


async def test_router_claude_error() -> None:
    stage, _, _ = _make_stage(error=RuntimeError("CLI not found"))
    result = await stage.execute(_make_input())

    assert result.success is False
    assert "Claude CLI" in result.error


async def test_router_json_parse_error() -> None:
    stage, _, _ = _make_stage(error=ValueError("No valid JSON"))
    result = await stage.execute(_make_input())

    assert result.success is False
    assert "파싱 실패" in result.error


async def test_router_saves_meta_json() -> None:
    stage, _, mock_fm = _make_stage()
    await stage.execute(_make_input())

    call_args = mock_fm.write_json.call_args
    saved_data = call_args[0][2]

    assert saved_data["slug"] == "what-is-ai"
    assert saved_data["topic"] == "AI란 무엇인가?"
    assert saved_data["category"] == "AI/ML"
    assert len(saved_data["seo_keywords"]) == 5
