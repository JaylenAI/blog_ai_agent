from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import settings
from app.models.base import Base

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
)


async def init_db() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
