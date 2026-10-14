from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from src.config.settings import settings
from src.models.base import Base

engine = create_async_engine(
    settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///").replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.app_env == "development",
    poolclass=NullPool if "sqlite" in settings.database_url else None,
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    await engine.dispose()