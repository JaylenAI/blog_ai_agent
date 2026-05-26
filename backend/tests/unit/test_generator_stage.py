from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

from app.pipeline.base import StageInput
from app.pipeline.stages.s4_generator import GeneratorStage, _extract_mermaid_blocks
from app.pipeline.stages.section_writer import SectionResult

MOCK_META = {
    "title": "AI란 무엇인가?",
    "seo_keywords": ["AI", "인공지능", "머신러닝"],
}

MOCK_OUTLINE = {
    "outline": [
        {
            "section_number": 1,
            "heading": "1. 들어가며",
            "key_points": ["AI의 정의", "왜 중요한가"],
        },
        {
            "section_number": 2,
            "heading": "2. AI의 기본 개념",
            "key_points": ["머신러닝", "딥러닝"],
        },
    ],
    "total_sections": 2,
}

MOCK_REFS = [
    {
        "url": "https://example.com/doc1",
        "title": "AI 공식 문서",
        "summary": "요약",
    }
]

SECTION_1_CONTENT = """## 1. 들어가며

인공지능(AI)은 현대 기술의 핵심입니다. AI가 왜 중요한지 알아봅시다."""

SECTION_2_CONTENT = """## 2. AI의 기본 개념

머신러닝과 딥러닝은 AI의 주요 분야입니다.

```mermaid
flowchart TD
    A[AI] --> B[ML]
    A --> C[DL]
```

이상으로 마치겠습니다."""


def _make_section_results(
    contents: list[str] | None = None,
    error_at: int | None = None,
) -> list[SectionResult]:
    if contents is None:
        contents = [SECTION_1_CONTENT, SECTION_2_CONTENT]
    results = []
    for i, content in enumerate(contents):
        if error_at is not None and i == error_at:
            results.append(SectionResult(
                section_number=i + 1,
                heading=f"섹션 {i + 1}",
                content="",
                success=False,
                error="CLI not found",
            ))
        else:
            results.append(SectionResult(
                section_number=i + 1,
                heading=f"섹션 {i + 1}",
                content=content,
                success=True,
                char_count=len(content),
            ))
    return results


@dataclass(frozen=True)
class MockClaudeResponse:
    text: str
    session_id: str = ""
    cost_usd: float = 0.0


def _make_stage(
    section_results: list[SectionResult] | None = None,
    outline: dict | None = None,
) -> tuple[GeneratorStage, AsyncMock, MagicMock]:
    mock_claude = AsyncMock()
    mock_fm = MagicMock()

    def read_json_side_effect(slug: str, filename: str) -> dict | list | None:
        if filename == "meta.json":
            return MOCK_META
        if filename == "outline.json":
            return outline if outline is not None else MOCK_OUTLINE
        if filename == "references.json":
            return MOCK_REFS
        return None

    mock_fm.read_json.side_effect = read_json_side_effect
    mock_fm.images_dir.return_value = MagicMock()

    stage = GeneratorStage(mock_claude, mock_fm)

    if section_results is None:
        section_results = _make_section_results()

    stage._writer = AsyncMock()
    stage._writer.write_section = AsyncMock(side_effect=section_results)

    return stage, mock_claude, mock_fm


def _make_input() -> StageInput:
    return StageInput(
        article_id=1,
        slug="ai란-무엇인가",
        topic="AI란 무엇인가?",
    )


async def test_generator_name() -> None:
    stage, _, _ = _make_stage()
    assert stage.name == "generator"


async def test_generator_success() -> None:
    stage, _, mock_fm = _make_stage()
    result = await stage.execute(_make_input())

    assert result.success is True
    assert result.stage_name == "generator"
    assert result.data["word_count"] > 0
    assert result.data["section_count"] == 2
    assert result.data["diagram_count"] == 1
    assert "content_path" in result.data

    stage._writer.write_section.assert_called()
    assert stage._writer.write_section.call_count == 2


async def test_generator_saves_final_md() -> None:
    stage, _, mock_fm = _make_stage()
    await stage.execute(_make_input())

    write_calls = mock_fm.write_text.call_args_list
    final_call = next(c for c in write_calls if c[0][1] == "final.md")
    assert "들어가며" in final_call[0][2]
    assert "AI의 기본 개념" in final_call[0][2]


async def test_generator_saves_mermaid_diagrams() -> None:
    stage, _, mock_fm = _make_stage()
    await stage.execute(_make_input())

    write_calls = mock_fm.write_text.call_args_list
    diagram_calls = [c for c in write_calls if "diagram" in c[0][1]]
    assert len(diagram_calls) == 1
    assert "flowchart TD" in diagram_calls[0][0][2]


async def test_generator_empty_outline() -> None:
    stage, _, _ = _make_stage(outline={"outline": []})
    result = await stage.execute(_make_input())

    assert result.success is False
    assert "아웃라인이 없습니다" in result.error


async def test_generator_missing_outline_file() -> None:
    stage, _, _ = _make_stage(outline={})
    result = await stage.execute(_make_input())

    assert result.success is False
    assert "아웃라인이 없습니다" in result.error


async def test_generator_section_write_failure() -> None:
    results = _make_section_results(error_at=0)
    stage, _, _ = _make_stage(section_results=results)
    result = await stage.execute(_make_input())

    assert result.success is False
    assert "섹션 1 작성 실패" in result.error


async def test_generator_second_section_failure() -> None:
    results = _make_section_results(error_at=1)
    stage, _, _ = _make_stage(section_results=results)
    result = await stage.execute(_make_input())

    assert result.success is False
    assert "섹션 2 작성 실패" in result.error


async def test_generator_no_diagrams() -> None:
    results = _make_section_results(contents=[
        "## 1. 들어가며\n\n본문입니다.",
        "## 2. 마치며\n\n끝입니다.",
    ])
    stage, _, mock_fm = _make_stage(section_results=results)
    result = await stage.execute(_make_input())

    assert result.success is True
    assert result.data["diagram_count"] == 0

    write_calls = mock_fm.write_text.call_args_list
    diagram_calls = [c for c in write_calls if "diagram" in c[0][1]]
    assert len(diagram_calls) == 0


async def test_generator_reads_all_files() -> None:
    stage, _, mock_fm = _make_stage()
    await stage.execute(_make_input())

    read_calls = mock_fm.read_json.call_args_list
    filenames = [c[0][1] for c in read_calls]
    assert "meta.json" in filenames
    assert "outline.json" in filenames
    assert "references.json" in filenames


async def test_generator_emits_progress() -> None:
    stage, _, _ = _make_stage()
    events = []
    await stage.execute(_make_input(), on_progress=lambda e: events.append(e))

    assert len(events) >= 5
    assert events[0].event_type == "stage_progress"
    assert "본문 작성 시작" in events[0].message
    assert "작성 중" in events[1].message
    assert "섹션 1/2 완료" in events[2].message
    assert "작성 중" in events[3].message
    assert "섹션 2/2 완료" in events[4].message


async def test_generator_passes_previous_sections() -> None:
    stage, _, _ = _make_stage()
    await stage.execute(_make_input())

    calls = stage._writer.write_section.call_args_list
    assert calls[0].kwargs["previous_sections"] == []
    assert len(calls[1].kwargs["previous_sections"]) == 1


def test_extract_mermaid_empty() -> None:
    assert _extract_mermaid_blocks("no mermaid here") == []


def test_extract_mermaid_single() -> None:
    content = "text\n```mermaid\nflowchart TD\n    A-->B\n```\nmore text"
    blocks = _extract_mermaid_blocks(content)
    assert len(blocks) == 1
    assert "flowchart TD" in blocks[0]


def test_extract_mermaid_multiple() -> None:
    content = (
        "```mermaid\nflowchart TD\n    A-->B\n```\n"
        "text\n"
        "```mermaid\nsequenceDiagram\n    A->>B: msg\n```"
    )
    blocks = _extract_mermaid_blocks(content)
    assert len(blocks) == 2
    assert "flowchart" in blocks[0]
    assert "sequenceDiagram" in blocks[1]


def test_extract_mermaid_unclosed_block() -> None:
    content = "```mermaid\nflowchart TD\n    A-->B"
    blocks = _extract_mermaid_blocks(content)
    assert len(blocks) == 0
