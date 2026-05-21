from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.models.validation import Validation


class ValidationRepository(BaseRepository[Validation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Validation)

    async def find_by_pipeline_run(self, run_id: int) -> Sequence[Validation]:
        stmt = (
            select(Validation)
            .where(Validation.pipeline_run_id == run_id)
            .order_by(Validation.id)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
