from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.models.pipeline_run import PipelineRun


class PipelineRepository(BaseRepository[PipelineRun]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, PipelineRun)

    async def find_by_article_id(
        self, article_id: int
    ) -> list[PipelineRun]:
        stmt = (
            select(PipelineRun)
            .where(PipelineRun.article_id == article_id)
            .order_by(PipelineRun.started_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_latest_by_article(
        self, article_id: int
    ) -> PipelineRun | None:
        stmt = (
            select(PipelineRun)
            .where(PipelineRun.article_id == article_id)
            .order_by(PipelineRun.started_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all_runs(
        self, *, limit: int = 50, offset: int = 0
    ) -> list[PipelineRun]:
        stmt = (
            select(PipelineRun)
            .order_by(PipelineRun.started_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_running(self) -> list[PipelineRun]:
        stmt = select(PipelineRun).where(
            PipelineRun.status == "running"
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_latest_active(self) -> PipelineRun | None:
        stmt = (
            select(PipelineRun)
            .where(
                PipelineRun.status.in_(["running", "paused", "pending"])
            )
            .order_by(PipelineRun.started_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
