from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from packages.ai_gateway.dependencies import get_ai_gateway_service
from packages.ai_gateway.service import AIGatewayService
from packages.common.db.dependencies import get_db_session
from packages.rag.orchestrator import RAGOrchestrator
from packages.rag.semantic_retriever import SemanticDocumentChunkRetriever
from packages.rag.vector_access_gateway import VectorAccessGateway


def get_vector_access_gateway(
    db_session: AsyncSession = Depends(get_db_session),
    ai_gateway_service: AIGatewayService = Depends(get_ai_gateway_service),
) -> VectorAccessGateway:
    retriever = SemanticDocumentChunkRetriever(
        session=db_session,
        ai_gateway_service=ai_gateway_service,
    )
    return VectorAccessGateway(retriever=retriever)


def get_rag_orchestrator(
    vector_access_gateway: VectorAccessGateway = Depends(get_vector_access_gateway),
    ai_gateway_service: AIGatewayService = Depends(get_ai_gateway_service),
) -> RAGOrchestrator:
    return RAGOrchestrator(
        vector_access_gateway=vector_access_gateway,
        ai_gateway_service=ai_gateway_service,
    )
