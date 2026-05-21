"""Repository 통합 테스트 — 실제 SQLite in-memory DB 사용."""

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.article_repo import ArticleRepository
from app.db.repositories.pipeline_repo import PipelineRepository
from app.db.repositories.validation_repo import ValidationRepository
from app.models.article import Article, ArticleStatus
from app.models.pipeline_run import (
    PipelineRun,
    PipelineStage,
    PipelineStatus,
)
from app.models.validation import Validation, ValidationCategory

# ── ArticleRepository ──


async def test_article_create_and_find_by_id(db_session: AsyncSession) -> None:
    repo = ArticleRepository(db_session)
    article = Article(slug="test-slug", title="테스트", topic="테스트 주제")
    created = await repo.create(article)

    assert created.id is not None
    found = await repo.find_by_id(created.id)
    assert found is not None
    assert found.slug == "test-slug"


async def test_article_find_by_slug(db_session: AsyncSession) -> None:
    repo = ArticleRepository(db_session)
    await repo.create(Article(slug="unique-slug", title="유니크", topic="유니크 주제"))

    found = await repo.find_by_slug("unique-slug")
    assert found is not None
    assert found.title == "유니크"

    not_found = await repo.find_by_slug("nonexistent")
    assert not_found is None


async def test_article_find_by_status(db_session: AsyncSession) -> None:
    repo = ArticleRepository(db_session)
    await repo.create(Article(slug="draft-1", title="D1", topic="t1", status=ArticleStatus.DRAFT))
    await repo.create(Article(slug="draft-2", title="D2", topic="t2", status=ArticleStatus.DRAFT))
    await repo.create(Article(slug="pub-1", title="P1", topic="t3", status=ArticleStatus.PUBLISHED))

    drafts = await repo.find_by_status(ArticleStatus.DRAFT)
    assert len(drafts) == 2

    published = await repo.find_by_status(ArticleStatus.PUBLISHED)
    assert len(published) == 1


async def test_article_find_all_pagination(db_session: AsyncSession) -> None:
    repo = ArticleRepository(db_session)
    for i in range(5):
        await repo.create(Article(slug=f"slug-{i}", title=f"T{i}", topic=f"topic-{i}"))

    page1 = await repo.find_all(offset=0, limit=3)
    assert len(page1) == 3

    page2 = await repo.find_all(offset=3, limit=3)
    assert len(page2) == 2


async def test_article_count(db_session: AsyncSession) -> None:
    repo = ArticleRepository(db_session)
    assert await repo.count() == 0

    await repo.create(Article(slug="s1", title="t", topic="t"))
    await repo.create(Article(slug="s2", title="t", topic="t"))
    assert await repo.count() == 2


async def test_article_delete(db_session: AsyncSession) -> None:
    repo = ArticleRepository(db_session)
    article = await repo.create(Article(slug="del-me", title="삭제", topic="삭제 주제"))

    await repo.delete(article)
    assert await repo.find_by_id(article.id) is None
    assert await repo.count() == 0


# ── PipelineRepository ──


async def test_pipeline_create_and_find_by_id(db_session: AsyncSession) -> None:
    article_repo = ArticleRepository(db_session)
    article = await article_repo.create(Article(slug="pipe-test", title="t", topic="t"))

    repo = PipelineRepository(db_session)
    run = await repo.create(PipelineRun(article_id=article.id))

    assert run.id is not None
    assert run.status == PipelineStatus.PENDING
    assert run.current_stage == PipelineStage.ROUTER

    found = await repo.find_by_id(run.id)
    assert found is not None
    assert found.article_id == article.id


async def test_pipeline_find_by_article_id(db_session: AsyncSession) -> None:
    article_repo = ArticleRepository(db_session)
    article = await article_repo.create(Article(slug="multi-run", title="t", topic="t"))

    repo = PipelineRepository(db_session)
    await repo.create(PipelineRun(article_id=article.id))
    await repo.create(PipelineRun(article_id=article.id))

    runs = await repo.find_by_article_id(article.id)
    assert len(runs) == 2


async def test_pipeline_find_latest_by_article(db_session: AsyncSession) -> None:
    from datetime import UTC, datetime, timedelta

    article_repo = ArticleRepository(db_session)
    article = await article_repo.create(Article(slug="latest-test", title="t", topic="t"))

    repo = PipelineRepository(db_session)
    now = datetime.now(UTC)
    await repo.create(PipelineRun(
        article_id=article.id,
        started_at=now - timedelta(minutes=5),
    ))
    run2 = await repo.create(PipelineRun(
        article_id=article.id,
        started_at=now,
    ))

    latest = await repo.find_latest_by_article(article.id)
    assert latest is not None
    assert latest.id == run2.id


async def test_pipeline_status_transitions(db_session: AsyncSession) -> None:
    article_repo = ArticleRepository(db_session)
    article = await article_repo.create(Article(slug="status-test", title="t", topic="t"))

    repo = PipelineRepository(db_session)
    run = await repo.create(PipelineRun(article_id=article.id))

    run.status = PipelineStatus.RUNNING
    run.current_stage = PipelineStage.RESEARCHER
    await db_session.flush()

    refreshed = await repo.find_by_id(run.id)
    assert refreshed is not None
    assert refreshed.status == PipelineStatus.RUNNING
    assert refreshed.current_stage == PipelineStage.RESEARCHER

    run.status = PipelineStatus.PAUSED
    run.current_stage = PipelineStage.GATE_ONE
    await db_session.flush()

    refreshed = await repo.find_by_id(run.id)
    assert refreshed is not None
    assert refreshed.status == PipelineStatus.PAUSED

    run.status = PipelineStatus.COMPLETED
    await db_session.flush()

    refreshed = await repo.find_by_id(run.id)
    assert refreshed is not None
    assert refreshed.status == PipelineStatus.COMPLETED


# ── ValidationRepository ──


async def test_validation_create_and_find_by_run(db_session: AsyncSession) -> None:
    article_repo = ArticleRepository(db_session)
    article = await article_repo.create(Article(slug="val-test", title="t", topic="t"))

    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(article_id=article.id))

    val_repo = ValidationRepository(db_session)
    v1 = await val_repo.create(Validation(
        pipeline_run_id=run.id,
        category=ValidationCategory.STYLE,
        item="격식체 사용",
        passed=True,
        score=0.95,
        message="격식체 확인됨",
    ))
    v2 = await val_repo.create(Validation(
        pipeline_run_id=run.id,
        category=ValidationCategory.SEO,
        item="키워드 밀도",
        passed=False,
        score=0.60,
        message="키워드 부족",
    ))

    results = await val_repo.find_by_pipeline_run(run.id)
    assert len(results) == 2
    assert results[0].id == v1.id
    assert results[1].id == v2.id


async def test_validation_empty_for_nonexistent_run(db_session: AsyncSession) -> None:
    val_repo = ValidationRepository(db_session)
    results = await val_repo.find_by_pipeline_run(9999)
    assert len(results) == 0


# ── Cascade Delete ──


async def test_cascade_delete_article_removes_runs_and_validations(
    db_session: AsyncSession,
) -> None:
    article_repo = ArticleRepository(db_session)
    article = await article_repo.create(Article(slug="cascade-test", title="t", topic="t"))

    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(article_id=article.id))

    val_repo = ValidationRepository(db_session)
    await val_repo.create(Validation(
        pipeline_run_id=run.id,
        category=ValidationCategory.STYLE,
        item="테스트",
        passed=True,
        score=1.0,
        message="OK",
    ))

    await article_repo.delete(article)

    assert await pipe_repo.find_by_id(run.id) is None
    assert len(await val_repo.find_by_pipeline_run(run.id)) == 0


async def test_cascade_delete_run_removes_validations(
    db_session: AsyncSession,
) -> None:
    article_repo = ArticleRepository(db_session)
    article = await article_repo.create(Article(slug="cascade-run", title="t", topic="t"))

    pipe_repo = PipelineRepository(db_session)
    run = await pipe_repo.create(PipelineRun(article_id=article.id))

    val_repo = ValidationRepository(db_session)
    await val_repo.create(Validation(
        pipeline_run_id=run.id,
        category=ValidationCategory.AEO,
        item="직접 답변",
        passed=True,
        score=0.8,
        message="OK",
    ))

    await pipe_repo.delete(run)
    assert len(await val_repo.find_by_pipeline_run(run.id)) == 0


# ── Unique Constraint ──


async def test_article_slug_unique_constraint(db_session: AsyncSession) -> None:
    repo = ArticleRepository(db_session)
    await repo.create(Article(slug="dup-slug", title="t1", topic="t1"))

    try:
        await repo.create(Article(slug="dup-slug", title="t2", topic="t2"))
        await db_session.flush()
        raise AssertionError("중복 slug에 예외가 발생해야 합니다")
    except sqlalchemy.exc.IntegrityError:
        await db_session.rollback()
