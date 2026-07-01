from packages.ai_gateway.dependencies import get_ai_gateway_service
from packages.ai_gateway.service import AIGatewayService
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.db.dependencies import get_db_session
from packages.ingestion.pipeline import DocumentIngestionPipeline
from packages.ingestion.repository import DocumentRepository
from packages.ingestion.service import DocumentIngestionService


def get_document_ingestion_service(
    db_session: AsyncSession = Depends(get_db_session),
    ai_gateway_service: AIGatewayService = Depends(get_ai_gateway_service),
) -> DocumentIngestionService:
    repository = DocumentRepository(session=db_session)
    pipeline = DocumentIngestionPipeline(ai_gateway_service=ai_gateway_service)
    return DocumentIngestionService(repository=repository, pipeline=pipeline)
