from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self._session = session
        self._model = model

    async def find_by_id(self, entity_id: int) -> T | None:
        return await self._session.get(self._model, entity_id)

    async def find_all(
        self, *, offset: int = 0, limit: int = 50
    ) -> Sequence[T]:
        stmt = (
            select(self._model)
            .offset(offset)
            .limit(limit)
            .order_by(self._model.id.desc())  # type: ignore[attr-defined]
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self._model)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def create(self, entity: T) -> T:
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity: T) -> None:
        await self._session.delete(entity)
        await self._session.flush()
