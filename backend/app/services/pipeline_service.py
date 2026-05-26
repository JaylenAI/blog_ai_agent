from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.claude.client import ClaudeClient
from app.config import settings
from app.db.repositories.article_repo import ArticleRepository
from app.db.repositories.pipeline_repo import PipelineRepository
from app.db.repositories.validation_repo import ValidationRepository
from app.exceptions import InvalidStateError, NotFoundError
from app.models.article import Article, ArticleStatus
from app.models.pipeline_run import PipelineRun, PipelineStage, PipelineStatus
from app.models.validation import Validation, ValidationCategory
from app.pipeline.base import PipelineEvent, Stage
from app.pipeline.gates.gate_one import GateOneStage
from app.pipeline.gates.gate_two import GateTwoStage
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.stages.s1_router import RouterStage
from app.pipeline.stages.s2_researcher import ResearcherStage
from app.pipeline.stages.s3_outliner import OutlinerStage
from app.pipeline.stages.s4_generator import GeneratorStage
from app.pipeline.stages.s5_validator import ValidatorStage
from app.pipeline.stages.s6_publisher import PublisherStage
from app.utils.file_manager import FileManager
from app.utils.logger import get_logger

logger = get_logger(__name__)

VALID_CATEGORIES = {c.value for c in ValidationCategory}


class PipelineService:
    def __init__(
        self,
        session: AsyncSession,
        claude: ClaudeClient,
        file_manager: FileManager,
    ) -> None:
        self._session = session
        self._claude = claude
        self._fm = file_manager
        self._article_repo = ArticleRepository(session)
        self._pipeline_repo = PipelineRepository(session)
        self._validation_repo = ValidationRepository(session)

    async def start_pipeline(
        self,
        article_id: int,
        *,
        auto_gate_one: bool = False,
        format_id: str | None = None,
    ) -> AsyncGenerator[PipelineEvent, None]:
        article = await self._article_repo.find_by_id(article_id)
        if not article:
            yield PipelineEvent(
                event_type="pipeline_error",
                stage="init",
                message=f"Article {article_id} not found",
            )
            return

        resolved_format = format_id or article.format_id

        pipeline_run = PipelineRun(article_id=article.id)
        pipeline_run = await self._pipeline_repo.create(pipeline_run)

        orchestrator = PipelineOrchestrator(
            self._build_all_stages(auto_gate_one=auto_gate_one)
        )

        async for event in orchestrator.execute(
            pipeline_run=pipeline_run,
            topic=article.topic,
            slug=article.slug,
            format_id=resolved_format,
            session=self._session,
        ):
            yield event

        await self._persist_metadata(article)
        await self._save_validations(pipeline_run.id, article.slug)

    async def resume_pipeline(
        self, run_id: int
    ) -> AsyncGenerator[PipelineEvent, None]:
        run = await self._pipeline_repo.find_by_id(run_id)
        if not run:
            yield PipelineEvent(
                event_type="pipeline_error",
                stage="resume",
                message="파이프라인 실행을 찾을 수 없습니다",
            )
            return

        if run.status != PipelineStatus.PAUSED:
            yield PipelineEvent(
                event_type="pipeline_error",
                stage="resume",
                message="파이프라인이 대기 상태가 아닙니다",
            )
            return

        article = await self._article_repo.find_by_id(run.article_id)
        if not article:
            yield PipelineEvent(
                event_type="pipeline_error",
                stage="resume",
                message="아티클을 찾을 수 없습니다",
            )
            return

        remaining = self._get_remaining_stages(run.current_stage)
        if not remaining:
            yield PipelineEvent(
                event_type="pipeline_error",
                stage="resume",
                message="재개할 스테이지가 없습니다",
            )
            return

        orchestrator = PipelineOrchestrator(remaining)

        async for event in orchestrator.execute(
            pipeline_run=run,
            topic=article.topic,
            slug=article.slug,
            format_id=article.format_id,
            session=self._session,
        ):
            yield event

        await self._persist_metadata(article)
        await self._save_validations(run.id, article.slug)

    async def reject_pipeline(self, run_id: int, *, feedback: str = "") -> None:
        run = await self._pipeline_repo.find_by_id(run_id)
        if not run:
            raise NotFoundError("파이프라인 실행을 찾을 수 없습니다")
        if run.status != PipelineStatus.PAUSED:
            raise InvalidStateError("파이프라인이 대기 상태가 아닙니다")
        run.status = PipelineStatus.CANCELLED
        if feedback:
            run.error_message = f"[피드백] {feedback}"
        await self._session.commit()

    async def reject_and_revise(
        self, run_id: int, *, feedback: str = ""
    ) -> AsyncGenerator[PipelineEvent, None]:
        run = await self._pipeline_repo.find_by_id(run_id)
        if not run:
            yield PipelineEvent(
                event_type="pipeline_error",
                stage="revise",
                message="파이프라인 실행을 찾을 수 없습니다",
            )
            return

        if run.status != PipelineStatus.PAUSED:
            yield PipelineEvent(
                event_type="pipeline_error",
                stage="revise",
                message="파이프라인이 대기 상태가 아닙니다",
            )
            return

        article = await self._article_repo.find_by_id(run.article_id)
        if not article:
            yield PipelineEvent(
                event_type="pipeline_error",
                stage="revise",
                message="아티클을 찾을 수 없습니다",
            )
            return

        run.status = PipelineStatus.CANCELLED
        run.error_message = f"[수정 요청] {feedback}" if feedback else "[수정 요청]"
        await self._session.flush()

        if feedback:
            self._fm.write_text(
                article.slug, "gate1_feedback.txt", feedback
            )

        new_run = PipelineRun(article_id=article.id)
        new_run = await self._pipeline_repo.create(new_run)

        stages: list[Stage] = [
            OutlinerStage(self._claude, self._fm),
            GateOneStage(),
        ]
        orchestrator = PipelineOrchestrator(stages)

        async for event in orchestrator.execute(
            pipeline_run=new_run,
            topic=article.topic,
            slug=article.slug,
            format_id=article.format_id,
            session=self._session,
        ):
            yield event

    async def cancel_run(self, run_id: int) -> None:
        run = await self._pipeline_repo.find_by_id(run_id)
        if not run:
            raise NotFoundError("파이프라인 실행을 찾을 수 없습니다")
        if run.status not in (PipelineStatus.RUNNING, PipelineStatus.PAUSED):
            raise InvalidStateError("취소 가능한 상태가 아닙니다")
        run.status = PipelineStatus.CANCELLED
        await self._session.commit()

    async def get_run(self, run_id: int) -> PipelineRun | None:
        return await self._pipeline_repo.find_by_id(run_id)

    async def get_active_run(self) -> PipelineRun | None:
        return await self._pipeline_repo.find_latest_active()

    async def get_all_runs(
        self, *, limit: int = 50, offset: int = 0
    ) -> list[PipelineRun]:
        return await self._pipeline_repo.find_all_runs(limit=limit, offset=offset)

    async def get_runs_for_article(self, article_id: int) -> list[PipelineRun]:
        return await self._pipeline_repo.find_by_article_id(article_id)

    async def retry_pipeline(
        self, run_id: int
    ) -> AsyncGenerator[PipelineEvent, None]:
        run = await self._pipeline_repo.find_by_id(run_id)
        if not run:
            yield PipelineEvent(
                event_type="pipeline_error",
                stage="retry",
                message="파이프라인 실행을 찾을 수 없습니다",
            )
            return

        if run.status != PipelineStatus.FAILED:
            yield PipelineEvent(
                event_type="pipeline_error",
                stage="retry",
                message="실패 상태의 파이프라인만 재시도할 수 있습니다",
            )
            return

        article = await self._article_repo.find_by_id(run.article_id)
        if not article:
            yield PipelineEvent(
                event_type="pipeline_error",
                stage="retry",
                message="아티클을 찾을 수 없습니다",
            )
            return

        previous_retries = await self._pipeline_repo.count_retries(article.id)
        if previous_retries >= settings.max_retry_count:
            yield PipelineEvent(
                event_type="pipeline_error",
                stage="retry",
                message=f"최대 재시도 횟수({settings.max_retry_count})를 초과했습니다",
            )
            return

        new_run = PipelineRun(
            article_id=article.id,
            retry_count=previous_retries + 1,
        )
        new_run = await self._pipeline_repo.create(new_run)

        orchestrator = PipelineOrchestrator(self._build_all_stages())

        async for event in orchestrator.execute(
            pipeline_run=new_run,
            topic=article.topic,
            slug=article.slug,
            format_id=article.format_id,
            session=self._session,
        ):
            yield event

        await self._persist_metadata(article)
        await self._save_validations(new_run.id, article.slug)

    async def validate_only(
        self, article_id: int
    ) -> AsyncGenerator[PipelineEvent, None]:
        article = await self._article_repo.find_by_id(article_id)
        if not article:
            yield PipelineEvent(
                event_type="pipeline_error",
                stage="validate",
                message="아티클을 찾을 수 없습니다",
            )
            return

        pipeline_run = PipelineRun(article_id=article.id)
        pipeline_run = await self._pipeline_repo.create(pipeline_run)

        stages: list[Stage] = [ValidatorStage(self._claude, self._fm)]
        orchestrator = PipelineOrchestrator(stages)

        async for event in orchestrator.execute(
            pipeline_run=pipeline_run,
            topic=article.topic,
            slug=article.slug,
            format_id=article.format_id,
            session=self._session,
        ):
            yield event

        await self._save_validations(pipeline_run.id, article.slug)

    async def get_validations(
        self, run_id: int
    ) -> Sequence[Validation]:
        return await self._validation_repo.find_by_pipeline_run(run_id)

    def _build_all_stages(self, *, auto_gate_one: bool = False) -> list[Stage]:
        return [
            RouterStage(self._claude, self._fm),
            ResearcherStage(self._claude, self._fm),
            OutlinerStage(self._claude, self._fm),
            GateOneStage(auto_approve=auto_gate_one),
            GeneratorStage(self._claude, self._fm),
            ValidatorStage(self._claude, self._fm),
            GateTwoStage(),
            PublisherStage(
                self._fm, obsidian_vault_path=settings.obsidian_vault_path
            ),
        ]

    def _get_remaining_stages(self, current_stage: PipelineStage) -> list[Stage]:
        if current_stage == PipelineStage.GATE_ONE:
            return [
                GeneratorStage(self._claude, self._fm),
                ValidatorStage(self._claude, self._fm),
                GateTwoStage(),
                PublisherStage(
                    self._fm, obsidian_vault_path=settings.obsidian_vault_path
                ),
            ]
        if current_stage == PipelineStage.GATE_TWO:
            return [
                PublisherStage(
                    self._fm, obsidian_vault_path=settings.obsidian_vault_path
                ),
            ]
        return []

    async def _persist_metadata(self, article: "Article") -> None:
        from datetime import UTC, datetime

        meta = self._fm.read_json(article.slug, "meta.json")
        if isinstance(meta, dict):
            tags = meta.get("seo_keywords", [])
            if isinstance(tags, list):
                article.tags = tags[:20]
            category = meta.get("category", "")
            if category and not article.category:
                article.category = category
            title = meta.get("title", "")
            if title and article.title == article.topic:
                article.title = title
            published_url = meta.get("published_url", "")
            if published_url:
                article.published_url = published_url
                article.published_at = datetime.now(UTC)
                article.status = ArticleStatus.PUBLISHED

        refs = self._fm.read_json(article.slug, "references.json")
        if isinstance(refs, list):
            article.reference_count = len(refs)

        outline = self._fm.read_json(article.slug, "outline.json")
        if isinstance(outline, dict):
            sections = outline.get("sections", [])
            if isinstance(sections, list):
                article.section_count = len(sections)

        content = self._fm.read_text(article.slug, "final.md")
        if content:
            article.word_count = len(content.replace(" ", "").replace("\n", ""))

        images = self._fm.list_images(article.slug)
        article.image_count = len(images)

        thumb = self._fm.images_dir(article.slug) / "thumbnail.png"
        if thumb.exists():
            article.thumbnail_path = f"{article.slug}/images/thumbnail.png"

        await self._session.flush()

    async def _save_validations(self, run_id: int, slug: str) -> None:
        existing = await self._validation_repo.find_by_pipeline_run(run_id)
        if existing:
            return

        critique = self._fm.read_json(slug, "critique.json")
        if not critique or not isinstance(critique, dict):
            return

        items = critique.get("validations", [])
        for item in items:
            category = item.get("category", "")
            if category not in VALID_CATEGORIES:
                continue
            validation = Validation(
                pipeline_run_id=run_id,
                category=ValidationCategory(category),
                item=item.get("item", ""),
                passed=bool(item.get("passed")),
                score=float(item.get("score", 0.0)),
                message=item.get("message", ""),
            )
            self._session.add(validation)

        await self._session.flush()
