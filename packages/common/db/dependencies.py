from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.db.session import build_session_factory


session_factory = build_session_factory()


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session