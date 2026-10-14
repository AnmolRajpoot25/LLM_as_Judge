import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from src.config.settings import settings, get_async_database_url
from src.models.base import Base

logger = logging.getLogger(__name__)

async_database_url = get_async_database_url(settings.database_url)

engine = create_async_engine(
    async_database_url,
    echo=settings.app_env == "development",
    poolclass=NullPool if "sqlite" in async_database_url else None,
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
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Async database tables initialized successfully.")
    except Exception as exc:
        logger.warning(f"Async database initialization notice: {exc}")


async def close_db() -> None:
    await engine.dispose()