"""PipelineService 통합 테스트 — 실제 DB + mock Claude/FileManager."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.article_repo import ArticleRepository
from app.db.repositories.pipeline_repo import PipelineRepository
from app.db.repositories.validation_repo import ValidationRepository
from app.exceptions import InvalidStateError, NotFoundError
from app.models.article import Article
from app.models.pipeline_run import PipelineRun, PipelineStage, PipelineStatus
from app.models.validation import ValidationCategory
from app.pipeline.base import PipelineEvent
from app.services.pipeline_service import PipelineService

from .conftest import (
    MOCK_CRITIQUE,
    MockClaudeResponse,
    build_mock_claude,
    build_mock_file_manager,
)


async def _create_test_article(session: AsyncSession) -> Article:
    repo = ArticleRepository(session)
    return await repo.create(
        Article(slug="test-llm", title="LLM이란 무엇인가", topic="LLM이란 무엇인가")
    )


async def _collect_events(
    service: PipelineService, article_id: int, **kwargs: object
) -> list[PipelineEvent]:
    events = []
    async for event in service.start_pipeline(article_id, **kwargs):
        events.append(event)
    return events


async def _collect_resume_events(service: PipelineService, run_id: int) -> list[PipelineEvent]:
    events = []
    async for event in service.resume_pipeline(run_id):
        events.append(event)
    return events


# ── start_pipeline ──


async def test_start_pipeline_pauses_at_gate_one(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    events = await _collect_events(service, article.id)

    event_types = [e.event_type for e in events]
    assert "gate_pending" in event_types
    assert "pipeline_complete" not in event_types

    gate_event = next(e for e in events if e.event_type == "gate_pending")
    assert gate_event.stage == "gate_one"

    pipe_repo = PipelineRepository(db_session)
    runs = await pipe_repo.find_by_article_id(article.id)
    assert len(runs) == 1
    assert runs[0].status == PipelineStatus.PAUSED
    assert runs[0].current_stage == PipelineStage.GATE_ONE


async def test_start_pipeline_auto_gate_one(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    mock_claude = build_mock_claude(full_pipeline=True)
    mock_fm = build_mock_file_manager(with_content=True)

    service = PipelineService(db_session, mock_claude, mock_fm)
    events = await _collect_events(service, article.id, auto_gate_one=True)

    event_types = [e.event_type for e in events]
    assert "gate_pending" in event_types
    gate_event = next(e for e in events if e.event_type == "gate_pending")
    assert gate_event.stage == "gate_two"


async def test_start_pipeline_article_not_found(db_session: AsyncSession) -> None:
    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    events = await _collect_events(service, 9999)

    assert len(events) == 1
    assert events[0].event_type == "pipeline_error"
    assert "not found" in events[0].message


async def test_start_pipeline_run_id_in_first_event(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    events = await _collect_events(service, article.id)

    first_start = next(e for e in events if e.event_type == "stage_start")
    assert "run_id" in first_start.data
    assert isinstance(first_start.data["run_id"], int)


async def test_start_pipeline_claude_failure(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    mock_claude = build_mock_claude()
    mock_claude.run_json.side_effect = RuntimeError("Claude CLI not found")
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    events = await _collect_events(service, article.id)

    event_types = [e.event_type for e in events]
    assert "stage_error" in event_types

    pipe_repo = PipelineRepository(db_session)
    runs = await pipe_repo.find_by_article_id(article.id)
    assert runs[0].status == PipelineStatus.FAILED
    assert "Claude CLI not found" in runs[0].error_message


# ── resume_pipeline ──


async def test_resume_from_gate_one(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()
    service = PipelineService(db_session, mock_claude, mock_fm)
    start_events = await _collect_events(service, article.id)

    gate_event = next(e for e in start_events if e.event_type == "gate_pending")
    assert gate_event.stage == "gate_one"

    pipe_repo = PipelineRepository(db_session)
    runs = await pipe_repo.find_by_article_id(article.id)
    run = runs[0]

    resume_claude = build_mock_claude(full_pipeline=True)
    resume_content = "# Generated Content\n\n" + "가" * 7000
    resume_claude.run_json.side_effect = [
        {"images": []},
        MOCK_CRITIQUE,
    ]
    resume_claude.run.return_value = MockClaudeResponse(text=resume_content)
    resume_fm = build_mock_file_manager(with_content=True)

    resume_service = PipelineService(db_session, resume_claude, resume_fm)
    resume_events = await _collect_resume_events(resume_service, run.id)

    event_types = [e.event_type for e in resume_events]
    assert "stage_start" in event_types
    assert "gate_pending" in event_types
    gate = next(e for e in resume_events if e.event_type == "gate_pending")
    assert gate.stage == "gate_two"


async def test_resume_from_gate_two(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)

    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(
        article_id=article.id,
        current_stage=PipelineStage.GATE_TWO,
        status=PipelineStatus.PAUSED,
    ))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager(with_content=True)

    service = PipelineService(db_session, mock_claude, mock_fm)
    events = await _collect_resume_events(service, run.id)

    event_types = [e.event_type for e in events]
    assert "stage_start" in event_types
    assert "pipeline_complete" in event_types

    refreshed = await pipe_repo.find_by_id(run.id)
    assert refreshed is not None
    assert refreshed.status == PipelineStatus.COMPLETED


async def test_resume_run_not_found(db_session: AsyncSession) -> None:
    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    events = await _collect_resume_events(service, 9999)

    assert len(events) == 1
    assert events[0].event_type == "pipeline_error"
    assert "찾을 수 없습니다" in events[0].message


async def test_resume_not_paused(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(
        article_id=article.id,
        status=PipelineStatus.RUNNING,
    ))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    events = await _collect_resume_events(service, run.id)

    assert len(events) == 1
    assert events[0].event_type == "pipeline_error"
    assert "대기 상태가 아닙니다" in events[0].message


async def test_resume_no_remaining_stages(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(
        article_id=article.id,
        current_stage=PipelineStage.PUBLISHER,
        status=PipelineStatus.PAUSED,
    ))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    events = await _collect_resume_events(service, run.id)

    assert len(events) == 1
    assert events[0].event_type == "pipeline_error"
    assert "재개할 스테이지가 없습니다" in events[0].message


# ── reject_pipeline ──


async def test_reject_pipeline(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(
        article_id=article.id,
        current_stage=PipelineStage.GATE_ONE,
        status=PipelineStatus.PAUSED,
    ))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    await service.reject_pipeline(run.id)

    refreshed = await pipe_repo.find_by_id(run.id)
    assert refreshed is not None
    assert refreshed.status == PipelineStatus.CANCELLED


async def test_reject_pipeline_not_found(db_session: AsyncSession) -> None:
    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    with pytest.raises(NotFoundError, match="찾을 수 없습니다"):
        await service.reject_pipeline(9999)


async def test_reject_pipeline_not_paused(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(
        article_id=article.id,
        status=PipelineStatus.COMPLETED,
    ))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    with pytest.raises(InvalidStateError, match="대기 상태가 아닙니다"):
        await service.reject_pipeline(run.id)


# ── get_run / get_validations ──


async def test_get_run(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(article_id=article.id))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    found = await service.get_run(run.id)
    assert found is not None
    assert found.id == run.id


async def test_get_run_not_found(db_session: AsyncSession) -> None:
    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    assert await service.get_run(9999) is None


async def test_get_validations(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(article_id=article.id))

    val_repo = ValidationRepository(db_session)
    from app.models.validation import Validation
    await val_repo.create(Validation(
        pipeline_run_id=run.id,
        category=ValidationCategory.STYLE,
        item="격식체",
        passed=True,
        score=0.9,
        message="OK",
    ))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    validations = await service.get_validations(run.id)
    assert len(validations) == 1
    assert validations[0].item == "격식체"


# ── _save_validations ──


async def test_save_validations_from_critique(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(article_id=article.id))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager(with_content=True)

    service = PipelineService(db_session, mock_claude, mock_fm)
    await service._save_validations(run.id, article.slug)

    val_repo = ValidationRepository(db_session)
    validations = await val_repo.find_by_pipeline_run(run.id)
    assert len(validations) == len(MOCK_CRITIQUE["validations"])

    categories = {v.category for v in validations}
    assert ValidationCategory.STYLE in categories
    assert ValidationCategory.SEO in categories


async def test_save_validations_idempotent(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(article_id=article.id))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager(with_content=True)

    service = PipelineService(db_session, mock_claude, mock_fm)
    await service._save_validations(run.id, article.slug)
    await service._save_validations(run.id, article.slug)

    val_repo = ValidationRepository(db_session)
    validations = await val_repo.find_by_pipeline_run(run.id)
    assert len(validations) == len(MOCK_CRITIQUE["validations"])


async def test_save_validations_no_critique_file(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(article_id=article.id))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    await service._save_validations(run.id, article.slug)

    val_repo = ValidationRepository(db_session)
    validations = await val_repo.find_by_pipeline_run(run.id)
    assert len(validations) == 0


async def test_save_validations_skips_invalid_category(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(article_id=article.id))

    from unittest.mock import MagicMock
    mock_claude = build_mock_claude()
    mock_fm = MagicMock()
    mock_fm.read_json.return_value = {
        "validations": [
            {
                "category": "unknown_cat",
                "item": "이상한 항목",
                "passed": True,
                "score": 1.0,
                "message": "OK",
            },
            {
                "category": "style",
                "item": "격식체",
                "passed": True,
                "score": 0.9,
                "message": "OK",
            },
        ]
    }

    service = PipelineService(db_session, mock_claude, mock_fm)
    await service._save_validations(run.id, article.slug)

    val_repo = ValidationRepository(db_session)
    validations = await val_repo.find_by_pipeline_run(run.id)
    assert len(validations) == 1
    assert validations[0].category == ValidationCategory.STYLE


# ── cancel_run ──


async def test_cancel_run_from_running(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(
        article_id=article.id,
        status=PipelineStatus.RUNNING,
    ))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    await service.cancel_run(run.id)

    refreshed = await pipe_repo.find_by_id(run.id)
    assert refreshed is not None
    assert refreshed.status == PipelineStatus.CANCELLED


async def test_cancel_run_from_paused(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(
        article_id=article.id,
        status=PipelineStatus.PAUSED,
    ))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    await service.cancel_run(run.id)

    refreshed = await pipe_repo.find_by_id(run.id)
    assert refreshed is not None
    assert refreshed.status == PipelineStatus.CANCELLED


async def test_cancel_run_not_found(db_session: AsyncSession) -> None:
    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    with pytest.raises(NotFoundError, match="찾을 수 없습니다"):
        await service.cancel_run(9999)


async def test_cancel_run_invalid_state_completed(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(
        article_id=article.id,
        status=PipelineStatus.COMPLETED,
    ))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    with pytest.raises(InvalidStateError, match="취소 가능한 상태가 아닙니다"):
        await service.cancel_run(run.id)


async def test_cancel_run_invalid_state_failed(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(
        article_id=article.id,
        status=PipelineStatus.FAILED,
    ))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    with pytest.raises(InvalidStateError, match="취소 가능한 상태가 아닙니다"):
        await service.cancel_run(run.id)


async def test_cancel_run_invalid_state_cancelled(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(
        article_id=article.id,
        status=PipelineStatus.CANCELLED,
    ))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    with pytest.raises(InvalidStateError, match="취소 가능한 상태가 아닙니다"):
        await service.cancel_run(run.id)


# ── get_all_runs / get_runs_for_article / get_active_run ──


async def test_get_all_runs(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    await pipe_repo.create(PipelineRun(article_id=article.id))
    await pipe_repo.create(PipelineRun(article_id=article.id))
    await pipe_repo.create(PipelineRun(article_id=article.id))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    runs = await service.get_all_runs(limit=2, offset=0)
    assert len(runs) == 2

    all_runs = await service.get_all_runs()
    assert len(all_runs) == 3


async def test_get_runs_for_article(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    await pipe_repo.create(PipelineRun(article_id=article.id))
    await pipe_repo.create(PipelineRun(article_id=article.id))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    runs = await service.get_runs_for_article(article.id)
    assert len(runs) == 2


async def test_get_runs_for_article_empty(db_session: AsyncSession) -> None:
    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    runs = await service.get_runs_for_article(9999)
    assert runs == []


async def test_get_active_run_returns_none(db_session: AsyncSession) -> None:
    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    active = await service.get_active_run()
    assert active is None


# ── retry_pipeline ──


async def _collect_retry_events(
    service: PipelineService, run_id: int
) -> list[PipelineEvent]:
    events = []
    async for event in service.retry_pipeline(run_id):
        events.append(event)
    return events


async def test_retry_pipeline_not_found(db_session: AsyncSession) -> None:
    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    events = await _collect_retry_events(service, 9999)

    assert len(events) == 1
    assert events[0].event_type == "pipeline_error"
    assert events[0].stage == "retry"
    assert "찾을 수 없습니다" in events[0].message


async def test_retry_pipeline_not_failed(db_session: AsyncSession) -> None:
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(
        article_id=article.id,
        status=PipelineStatus.COMPLETED,
    ))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    events = await _collect_retry_events(service, run.id)

    assert len(events) == 1
    assert events[0].event_type == "pipeline_error"
    assert "실패 상태의 파이프라인만" in events[0].message


async def test_retry_pipeline_article_deleted(db_session: AsyncSession) -> None:
    """retry 시 article이 삭제된 경우"""
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(
        article_id=article.id,
        status=PipelineStatus.FAILED,
    ))

    # article 삭제 시뮬레이션: article_repo mock
    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()
    service = PipelineService(db_session, mock_claude, mock_fm)

    from unittest.mock import AsyncMock
    service._article_repo.find_by_id = AsyncMock(return_value=None)

    events = await _collect_retry_events(service, run.id)

    assert len(events) == 1
    assert events[0].event_type == "pipeline_error"
    assert "아티클을 찾을 수 없습니다" in events[0].message


async def test_retry_pipeline_success(db_session: AsyncSession) -> None:
    """FAILED 상태 run을 retry하면 새 run이 생성되고 파이프라인 시작"""
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    failed_run = await pipe_repo.create(PipelineRun(
        article_id=article.id,
        status=PipelineStatus.FAILED,
    ))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    events = await _collect_retry_events(service, failed_run.id)

    event_types = [e.event_type for e in events]
    assert "stage_start" in event_types

    all_runs = await pipe_repo.find_by_article_id(article.id)
    assert len(all_runs) == 2
    run_ids = {r.id for r in all_runs}
    assert failed_run.id in run_ids


# ── validate_only ──


async def _collect_validate_only_events(
    service: PipelineService, article_id: int
) -> list[PipelineEvent]:
    events = []
    async for event in service.validate_only(article_id):
        events.append(event)
    return events


async def test_validate_only_article_not_found(db_session: AsyncSession) -> None:
    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()

    service = PipelineService(db_session, mock_claude, mock_fm)
    events = await _collect_validate_only_events(service, 9999)

    assert len(events) == 1
    assert events[0].event_type == "pipeline_error"
    assert events[0].stage == "validate"
    assert "아티클을 찾을 수 없습니다" in events[0].message


async def test_validate_only_success(db_session: AsyncSession) -> None:
    """validate_only는 ValidatorStage만 실행"""
    article = await _create_test_article(db_session)

    mock_claude = build_mock_claude()
    mock_claude.run_json.side_effect = [MOCK_CRITIQUE]
    mock_fm = build_mock_file_manager(with_content=True)

    service = PipelineService(db_session, mock_claude, mock_fm)
    events = await _collect_validate_only_events(service, article.id)

    event_types = [e.event_type for e in events]
    assert "stage_start" in event_types

    pipe_repo = PipelineRepository(db_session)
    runs = await pipe_repo.find_by_article_id(article.id)
    assert len(runs) == 1


# ── resume_pipeline: article 삭제된 경우 ──


async def test_resume_pipeline_article_deleted(db_session: AsyncSession) -> None:
    """resume 시 article이 삭제된 경우"""
    article = await _create_test_article(db_session)
    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(
        article_id=article.id,
        current_stage=PipelineStage.GATE_ONE,
        status=PipelineStatus.PAUSED,
    ))

    mock_claude = build_mock_claude()
    mock_fm = build_mock_file_manager()
    service = PipelineService(db_session, mock_claude, mock_fm)

    from unittest.mock import AsyncMock
    service._article_repo.find_by_id = AsyncMock(return_value=None)

    events = await _collect_resume_events(service, run.id)

    assert len(events) == 1
    assert events[0].event_type == "pipeline_error"
    assert "아티클을 찾을 수 없습니다" in events[0].message
