from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.db.dependencies import get_db_session
from packages.ingestion.repository import DocumentRepository
from packages.ingestion.service import DocumentIngestionService


def get_document_ingestion_service(
    db_session: AsyncSession = Depends(get_db_session),
) -> DocumentIngestionService:
    repository = DocumentRepository(session=db_session)
    return DocumentIngestionService(repository=repository)
