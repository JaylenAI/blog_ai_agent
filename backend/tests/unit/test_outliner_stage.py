from unittest.mock import AsyncMock, MagicMock

from app.pipeline.base import StageInput
from app.pipeline.stages.s3_outliner import OutlinerStage

MOCK_META = {
    "slug": "what-is-ai",
    "title": "AI란 무엇인가? — 2026년 개발자 필수 가이드",
    "category": "AI/ML",
    "target_audience": "beginner",
    "seo_keywords": ["AI", "인공지능"],
}

MOCK_REFS = [
    {
        "url": "https://example.com/doc1",
        "title": "AI 공식 문서",
        "summary": "AI 핵심 개념 요약",
    }
]

MOCK_OUTLINE_RESPONSE = {
    "outline": [
        {
            "section_number": 1,
            "heading": "1. 들어가며",
            "key_points": ["AI의 정의", "왜 중요한가", "글의 구조 안내"],
            "estimated_words": 500,
            "reference_urls": [],
        },
        {
            "section_number": 2,
            "heading": "2. AI의 기본 개념",
            "key_points": ["머신러닝", "딥러닝", "LLM"],
            "estimated_words": 1000,
            "reference_urls": ["https://example.com/doc1"],
        },
        {
            "section_number": 7,
            "heading": "7. 마치며",
            "key_points": ["핵심 요약", "실천 방안"],
            "estimated_words": 500,
            "reference_urls": [],
        },
    ],
    "total_sections": 7,
    "estimated_total_words": 7000,
    "approach": "설명형",
}


def _make_stage(
    response: dict | None = None,
    error: Exception | None = None,
    meta: dict | list | None = None,
    refs: dict | list | None = None,
) -> tuple[OutlinerStage, AsyncMock, MagicMock]:
    mock_claude = AsyncMock()
    if error:
        mock_claude.run_json.side_effect = error
    else:
        mock_claude.run_json.return_value = response or MOCK_OUTLINE_RESPONSE

    mock_fm = MagicMock()

    def read_json_side_effect(slug: str, filename: str) -> dict | list | None:
        if filename == "meta.json":
            return meta if meta is not None else MOCK_META
        if filename == "references.json":
            return refs if refs is not None else MOCK_REFS
        return None

    mock_fm.read_json.side_effect = read_json_side_effect

    return OutlinerStage(mock_claude, mock_fm), mock_claude, mock_fm


def _make_input() -> StageInput:
    return StageInput(
        article_id=1,
        slug="ai란-무엇인가",
        topic="AI란 무엇인가?",
        data={"references": MOCK_REFS},
    )


async def test_outliner_name() -> None:
    stage, _, _ = _make_stage()
    assert stage.name == "outliner"


async def test_outliner_success() -> None:
    stage, mock_claude, mock_fm = _make_stage()
    result = await stage.execute(_make_input())

    assert result.success is True
    assert result.stage_name == "outliner"
    assert result.data["total_sections"] == 7
    assert result.data["estimated_total_words"] == 7000
    assert len(result.data["outline"]) == 3

    mock_claude.run_json.assert_called_once()
    mock_fm.write_json.assert_called_once()


async def test_outliner_saves_outline_json() -> None:
    stage, _, mock_fm = _make_stage()
    await stage.execute(_make_input())

    call_args = mock_fm.write_json.call_args[0]
    assert call_args[0] == "ai란-무엇인가"
    assert call_args[1] == "outline.json"
    assert call_args[2]["total_sections"] == 7


async def test_outliner_missing_fields() -> None:
    stage, _, _ = _make_stage(response={"outline": []})
    result = await stage.execute(_make_input())

    assert result.success is False
    assert "필수 필드 누락" in result.error


async def test_outliner_claude_error() -> None:
    stage, _, _ = _make_stage(error=RuntimeError("CLI not found"))
    result = await stage.execute(_make_input())

    assert result.success is False
    assert "Outliner 응답 처리 실패" in result.error


async def test_outliner_json_parse_error() -> None:
    stage, _, _ = _make_stage(error=ValueError("No valid JSON"))
    result = await stage.execute(_make_input())

    assert result.success is False
    assert "Outliner 응답 처리 실패" in result.error


async def test_outliner_reads_meta_and_refs() -> None:
    stage, _, mock_fm = _make_stage()
    await stage.execute(_make_input())

    read_calls = mock_fm.read_json.call_args_list
    filenames = [c[0][1] for c in read_calls]
    assert "meta.json" in filenames
    assert "references.json" in filenames


async def test_outliner_handles_missing_meta() -> None:
    stage, mock_claude, _ = _make_stage(meta=None)
    await stage.execute(_make_input())

    prompt = mock_claude.run_json.call_args[0][0]
    assert "AI란 무엇인가?" in prompt


async def test_outliner_handles_empty_refs() -> None:
    stage, mock_claude, _ = _make_stage(refs=[])
    await stage.execute(_make_input())

    prompt = mock_claude.run_json.call_args[0][0]
    assert "참고자료 없음" in prompt


async def test_outliner_prompt_contains_topic() -> None:
    stage, mock_claude, _ = _make_stage()
    await stage.execute(_make_input())

    prompt = mock_claude.run_json.call_args[0][0]
    assert "AI란 무엇인가?" in prompt
    assert "AI/ML" in prompt
    assert "beginner" in prompt
