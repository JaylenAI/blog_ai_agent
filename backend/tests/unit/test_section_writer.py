from dataclasses import dataclass
from unittest.mock import AsyncMock

from app.pipeline.stages.section_writer import (
    MAX_SECTION_RETRIES,
    MIN_SECTION_CHARS,
    SectionWriter,
)


@dataclass(frozen=True)
class MockClaudeResponse:
    text: str
    session_id: str = ""
    cost_usd: float = 0.0


VALID_SECTION_TEXT = "A" * (MIN_SECTION_CHARS + 50)

SECTION_KWARGS = {
    "topic": "AI란 무엇인가?",
    "title": "AI의 기초",
    "section": {"heading": "1. 들어가며", "key_points": ["AI 정의"]},
    "section_number": 1,
    "total_sections": 3,
    "previous_sections": [],
    "references": "참고자료 없음",
    "seo_keywords": "AI, 인공지능",
    "format_spec": None,
    "full_outline": "## 1. 들어가며\n  - AI 정의",
}


def _make_writer(
    responses: list[str] | None = None,
    error: Exception | None = None,
) -> tuple[SectionWriter, AsyncMock]:
    mock_claude = AsyncMock()
    mock_prompt = AsyncMock()
    mock_prompt.render_section = lambda **kwargs: f"prompt for {kwargs.get('section_heading')}"

    if error:
        mock_claude.run.side_effect = error
    elif responses:
        mock_claude.run.side_effect = [
            MockClaudeResponse(text=r) for r in responses
        ]
    else:
        mock_claude.run.return_value = MockClaudeResponse(text=VALID_SECTION_TEXT)

    return SectionWriter(mock_claude, mock_prompt), mock_claude


async def test_successful_write() -> None:
    writer, mock_claude = _make_writer()
    result = await writer.write_section(**SECTION_KWARGS)

    assert result.success is True
    assert result.heading == "1. 들어가며"
    assert result.section_number == 1
    assert result.char_count == len(VALID_SECTION_TEXT)
    assert result.retry_count == 0
    mock_claude.run.assert_called_once()


async def test_retry_on_short_content() -> None:
    short = "짧은 내용"
    writer, mock_claude = _make_writer(
        responses=[short, short, VALID_SECTION_TEXT]
    )
    result = await writer.write_section(**SECTION_KWARGS)

    assert result.success is True
    assert result.retry_count == 2
    assert mock_claude.run.call_count == 3


async def test_fail_after_max_retries_short() -> None:
    short = "짧음"
    writer, mock_claude = _make_writer(
        responses=[short] * (MAX_SECTION_RETRIES + 1)
    )
    result = await writer.write_section(**SECTION_KWARGS)

    assert result.success is False
    assert "너무 짧습니다" in result.error
    assert result.retry_count == MAX_SECTION_RETRIES + 1


async def test_runtime_error_fails_immediately() -> None:
    writer, mock_claude = _make_writer(error=RuntimeError("CLI timeout"))
    result = await writer.write_section(**SECTION_KWARGS)

    assert result.success is False
    assert "CLI timeout" in result.error
    mock_claude.run.assert_called_once()


async def test_timeout_error_fails_immediately() -> None:
    writer, mock_claude = _make_writer(error=TimeoutError("timed out"))
    result = await writer.write_section(**SECTION_KWARGS)

    assert result.success is False
    assert "timed out" in result.error
    mock_claude.run.assert_called_once()


async def test_content_is_stripped() -> None:
    padded = f"  \n{VALID_SECTION_TEXT}\n  "
    writer, _ = _make_writer(responses=[padded])
    result = await writer.write_section(**SECTION_KWARGS)

    assert result.success is True
    assert result.content == VALID_SECTION_TEXT


async def test_heading_from_section_dict() -> None:
    writer, _ = _make_writer()
    kwargs = {**SECTION_KWARGS, "section": {"heading": "커스텀 제목"}}
    result = await writer.write_section(**kwargs)

    assert result.heading == "커스텀 제목"


async def test_heading_fallback_no_heading() -> None:
    writer, _ = _make_writer()
    kwargs = {**SECTION_KWARGS, "section": {"key_points": ["포인트"]}}
    result = await writer.write_section(**kwargs)

    assert result.heading == "섹션 1"
