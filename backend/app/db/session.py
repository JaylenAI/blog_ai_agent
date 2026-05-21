from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.engine import engine

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
