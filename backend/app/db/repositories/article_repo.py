from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.models.article import Article, ArticleStatus


class ArticleRepository(BaseRepository[Article]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Article)

    async def find_by_slug(self, slug: str) -> Article | None:
        stmt = select(Article).where(Article.slug == slug)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_status(
        self, status: ArticleStatus
    ) -> list[Article]:
        stmt = (
            select(Article)
            .where(Article.status == status)
            .order_by(Article.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
