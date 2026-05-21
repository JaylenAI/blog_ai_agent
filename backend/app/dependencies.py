from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.article_repo import ArticleRepository
from app.db.repositories.pipeline_repo import PipelineRepository
from app.db.session import async_session_factory
from app.services.article_service import ArticleService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_article_repo(
    db: AsyncSession = Depends(get_db),
) -> ArticleRepository:
    return ArticleRepository(db)


async def get_pipeline_repo(
    db: AsyncSession = Depends(get_db),
) -> PipelineRepository:
    return PipelineRepository(db)


async def get_article_service(
    repo: ArticleRepository = Depends(get_article_repo),
) -> ArticleService:
    return ArticleService(repo)
