"""Generator stage_progress 실시간 이벤트 흐름 E2E 통합 테스트.

실제 DB + mock Claude/FileManager 환경에서
Gate 1 승인 → Generator → 섹션별 stage_progress 이벤트 검증.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.article_repo import ArticleRepository
from app.db.repositories.pipeline_repo import PipelineRepository
from app.models.article import Article
from app.models.pipeline_run import PipelineRun, PipelineStage, PipelineStatus
from app.pipeline.base import PipelineEvent
from app.services.pipeline_service import PipelineService

from .conftest import (
    MOCK_CRITIQUE,
    MOCK_OUTLINE_RESPONSE,
    MockClaudeResponse,
    build_mock_claude,
    build_mock_file_manager,
)

SECTION_CONTENT = "가" * 800


async def _create_article(session: AsyncSession) -> Article:
    repo = ArticleRepository(session)
    return await repo.create(
        Article(slug="test-progress", title="진행률 테스트", topic="진행률 테스트")
    )


async def _start_and_pause_at_gate1(
    session: AsyncSession, article: Article
) -> PipelineRun:
    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()
    service = PipelineService(session, mock_claude, mock_fm)

    events = []
    async for event in service.start_pipeline(article.id):
        events.append(event)

    gate = next(e for e in events if e.event_type == "gate_pending")
    assert gate.stage == "gate_one"

    repo = PipelineRepository(session)
    runs = await repo.find_by_article_id(article.id)
    run = runs[0]
    assert run.status == PipelineStatus.PAUSED
    assert run.current_stage == PipelineStage.GATE_ONE
    return run


def _build_resume_mocks():
    mock_claude = build_mock_claude(full_pipeline=True)
    mock_claude.run_json.side_effect = [
        {"images": []},
        MOCK_CRITIQUE,
    ]
    mock_claude.run.return_value = MockClaudeResponse(text=SECTION_CONTENT)

    mock_fm = build_mock_file_manager(with_content=True)
    return mock_claude, mock_fm


async def _resume_and_collect(
    session: AsyncSession, run_id: int
) -> list[PipelineEvent]:
    mock_claude, mock_fm = _build_resume_mocks()
    service = PipelineService(session, mock_claude, mock_fm)

    events = []
    async for event in service.resume_pipeline(run_id):
        events.append(event)
    return events


async def test_generator_emits_stage_progress_events(
    db_session: AsyncSession,
) -> None:
    article = await _create_article(db_session)
    run = await _start_and_pause_at_gate1(db_session, article)
    events = await _resume_and_collect(db_session, run.id)

    progress_events = [
        e for e in events if e.event_type == "stage_progress"
    ]

    assert len(progress_events) > 0, "stage_progress 이벤트가 없음"

    total_sections = MOCK_OUTLINE_RESPONSE["total_sections"]

    first = progress_events[0]
    assert first.stage == "generator"
    assert "본문 작성 시작" in first.message
    assert first.data["total_sections"] == total_sections
    assert first.data["completed_sections"] == 0


async def test_generator_progress_writing_then_done_per_section(
    db_session: AsyncSession,
) -> None:
    article = await _create_article(db_session)
    run = await _start_and_pause_at_gate1(db_session, article)
    events = await _resume_and_collect(db_session, run.id)

    progress_events = [
        e for e in events
        if e.event_type == "stage_progress" and e.stage == "generator"
    ]

    total = MOCK_OUTLINE_RESPONSE["total_sections"]

    writing_events = [
        e for e in progress_events if e.data.get("status") == "writing"
    ]
    done_events = [
        e for e in progress_events if "완료" in e.message
    ]

    assert len(writing_events) == total, (
        f"writing 이벤트 {len(writing_events)}개, 예상 {total}개"
    )
    assert len(done_events) == total, (
        f"완료 이벤트 {len(done_events)}개, 예상 {total}개"
    )

    for i, we in enumerate(writing_events):
        assert we.data["current_section"] == i + 1
        assert we.data["completed_sections"] == i

    for i, de in enumerate(done_events):
        assert de.data["completed_sections"] == i + 1
        assert de.data["section_heading"] != ""


async def test_generator_progress_ordering(
    db_session: AsyncSession,
) -> None:
    article = await _create_article(db_session)
    run = await _start_and_pause_at_gate1(db_session, article)
    events = await _resume_and_collect(db_session, run.id)

    progress_events = [
        e for e in events
        if e.event_type == "stage_progress" and e.stage == "generator"
    ]

    completed_sequence = []
    for e in progress_events:
        if "completed_sections" in e.data:
            completed_sequence.append(e.data["completed_sections"])

    for i in range(1, len(completed_sequence)):
        diff = completed_sequence[i] - completed_sequence[i - 1]
        assert diff in (0, 1), (
            f"completed_sections가 비정상 점프: "
            f"{completed_sequence[i-1]} → {completed_sequence[i]}"
        )


async def test_generator_progress_reaches_completion(
    db_session: AsyncSession,
) -> None:
    article = await _create_article(db_session)
    run = await _start_and_pause_at_gate1(db_session, article)
    events = await _resume_and_collect(db_session, run.id)

    progress_events = [
        e for e in events
        if e.event_type == "stage_progress" and e.stage == "generator"
    ]

    total = MOCK_OUTLINE_RESPONSE["total_sections"]

    last_progress = progress_events[-1]
    assert last_progress.data["completed_sections"] == total, (
        f"마지막 이벤트 completed={last_progress.data['completed_sections']}, "
        f"예상={total}"
    )

    stage_complete = next(
        (e for e in events
         if e.event_type == "stage_complete" and e.stage == "generator"),
        None,
    )
    assert stage_complete is not None, "generator stage_complete 이벤트 없음"


async def test_generator_progress_section_headings_match_outline(
    db_session: AsyncSession,
) -> None:
    article = await _create_article(db_session)
    run = await _start_and_pause_at_gate1(db_session, article)
    events = await _resume_and_collect(db_session, run.id)

    writing_events = [
        e for e in events
        if e.event_type == "stage_progress"
        and e.stage == "generator"
        and e.data.get("status") == "writing"
    ]

    outline_headings = [
        s["heading"] for s in MOCK_OUTLINE_RESPONSE["outline"]
    ]

    for we, expected_heading in zip(writing_events, outline_headings):
        assert we.data["section_heading"] == expected_heading, (
            f"이벤트 heading '{we.data['section_heading']}' != "
            f"아웃라인 '{expected_heading}'"
        )


async def test_pipeline_completes_after_generator_progress(
    db_session: AsyncSession,
) -> None:
    article = await _create_article(db_session)
    run = await _start_and_pause_at_gate1(db_session, article)
    events = await _resume_and_collect(db_session, run.id)

    event_types = [e.event_type for e in events]

    assert "stage_start" in event_types
    assert "stage_progress" in event_types

    gate_two = next(
        (e for e in events if e.event_type == "gate_pending"),
        None,
    )
    assert gate_two is not None
    assert gate_two.stage == "gate_two"

    repo = PipelineRepository(db_session)
    refreshed = await repo.find_by_id(run.id)
    assert refreshed is not None
    assert refreshed.status == PipelineStatus.PAUSED
    assert refreshed.current_stage == PipelineStage.GATE_TWO
