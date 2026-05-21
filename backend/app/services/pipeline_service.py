from collections.abc import AsyncGenerator, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.claude.client import ClaudeClient
from app.config import settings
from app.db.repositories.article_repo import ArticleRepository
from app.db.repositories.pipeline_repo import PipelineRepository
from app.db.repositories.validation_repo import ValidationRepository
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
        self, article_id: int, *, auto_gate_one: bool = False
    ) -> AsyncGenerator[PipelineEvent, None]:
        article = await self._article_repo.find_by_id(article_id)
        if not article:
            yield PipelineEvent(
                event_type="pipeline_error",
                stage="init",
                message=f"Article {article_id} not found",
            )
            return

        pipeline_run = PipelineRun(article_id=article.id)
        pipeline_run = await self._pipeline_repo.create(pipeline_run)

        orchestrator = PipelineOrchestrator(
            self._build_all_stages(auto_gate_one=auto_gate_one)
        )

        async for event in orchestrator.execute(
            pipeline_run=pipeline_run,
            topic=article.topic,
            slug=article.slug,
            session=self._session,
        ):
            yield event

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
            session=self._session,
        ):
            yield event

        await self._save_validations(run.id, article.slug)

    async def reject_pipeline(self, run_id: int) -> None:
        run = await self._pipeline_repo.find_by_id(run_id)
        if not run:
            raise ValueError("파이프라인 실행을 찾을 수 없습니다")
        if run.status != PipelineStatus.PAUSED:
            raise ValueError("파이프라인이 대기 상태가 아닙니다")
        run.status = PipelineStatus.CANCELLED
        await self._session.flush()

    async def get_run(self, run_id: int) -> PipelineRun | None:
        return await self._pipeline_repo.find_by_id(run_id)

    async def get_runs_for_article(self, article_id: int) -> list[PipelineRun]:
        return await self._pipeline_repo.find_by_article_id(article_id)

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
