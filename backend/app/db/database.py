from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, async_engine_from_config
from sqlalchemy.orm import declarative_base
from app.core.config import get_settings
import os

settings = get_settings()

# 使用 asyncpg 驱动
_database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
engine = create_async_engine(_database_url, echo=settings.DEBUG)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
