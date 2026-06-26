from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.db.dependencies import get_db_session


router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    db_session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    return {"status": "ok"}