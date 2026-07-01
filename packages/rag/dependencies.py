from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.db.dependencies import get_db_session
from packages.rag.retriever import DocumentChunkRetriever
from packages.rag.vector_access_gateway import VectorAccessGateway


def get_vector_access_gateway(
    db_session: AsyncSession = Depends(get_db_session),
) -> VectorAccessGateway:
    retriever = DocumentChunkRetriever(session=db_session)
    return VectorAccessGateway(retriever=retriever)