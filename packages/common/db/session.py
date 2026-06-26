from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from packages.common.config import settings


def build_engine(database_url: str | None = None) -> AsyncEngine:
    url = database_url or settings.database_url
    return create_async_engine(url)


def build_session_factory(database_url: str | None = None) -> async_sessionmaker[AsyncSession]:
    engine = build_engine(database_url)
    return async_sessionmaker(bind=engine)