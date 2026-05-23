from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.claude.client import ClaudeClient
from app.db.repositories.article_repo import ArticleRepository
from app.db.repositories.pipeline_repo import PipelineRepository
from app.db.session import async_session_factory
from app.services.article_service import ArticleService
from app.services.pipeline_service import PipelineService
from app.utils.file_manager import FileManager


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


def get_claude_client() -> ClaudeClient:
    return ClaudeClient()


def get_file_manager() -> FileManager:
    return FileManager()


async def get_article_service(
    repo: ArticleRepository = Depends(get_article_repo),
    fm: FileManager = Depends(get_file_manager),
) -> ArticleService:
    return ArticleService(repo, fm)


async def get_pipeline_service(
    db: AsyncSession = Depends(get_db),
    claude: ClaudeClient = Depends(get_claude_client),
    fm: FileManager = Depends(get_file_manager),
) -> PipelineService:
    return PipelineService(db, claude, fm)


def create_pipeline_service(session: AsyncSession) -> PipelineService:
    return PipelineService(session, ClaudeClient(), FileManager())
