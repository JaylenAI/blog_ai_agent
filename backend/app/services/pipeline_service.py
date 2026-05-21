from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.claude.client import ClaudeClient
from app.db.repositories.article_repo import ArticleRepository
from app.db.repositories.pipeline_repo import PipelineRepository
from app.models.pipeline_run import PipelineRun
from app.pipeline.base import PipelineEvent
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.stages.s1_router import RouterStage
from app.utils.file_manager import FileManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


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

    async def start_pipeline(
        self, article_id: int
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

        orchestrator = PipelineOrchestrator([
            RouterStage(self._claude, self._fm),
        ])

        async for event in orchestrator.execute(
            pipeline_run=pipeline_run,
            topic=article.topic,
            slug=article.slug,
            session=self._session,
        ):
            yield event

    async def get_run(self, run_id: int) -> PipelineRun | None:
        return await self._pipeline_repo.find_by_id(run_id)

    async def get_runs_for_article(self, article_id: int) -> list[PipelineRun]:
        return await self._pipeline_repo.find_by_article_id(article_id)
