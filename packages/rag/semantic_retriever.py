from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.ai_gateway.contracts import EmbeddingRequest
from packages.ai_gateway.service import AIGatewayService
from packages.common.db.models import Document, DocumentChunk
from packages.rag.contracts import RetrievedChunk, RetrievalFilters, RetrievalResult
from packages.security.tenant_context import TenantContext


class SemanticDocumentChunkRetriever:
    def __init__(
        self,
        session: AsyncSession,
        ai_gateway_service: AIGatewayService,
    ) -> None:
        self._session = session
        self._ai_gateway_service = ai_gateway_service

    async def search(
        self,
        *,
        tenant_context: TenantContext,
        query_text: str,
        top_k: int,
        filters: RetrievalFilters,
    ) -> RetrievalResult:
        query_embedding = await self._generate_query_embedding(
            tenant_context=tenant_context,
            query_text=query_text,
        )

        statement = self._build_statement(
            tenant_context=tenant_context,
            filters=filters,
        )

        result = await self._session.execute(statement)
        rows = result.scalars().all()

        scored_chunks = [
            RetrievedChunk(
                chunk_id=row.chunk_id,
                document_id=row.document_id,
                version=row.version,
                tenant_id=row.tenant_id,
                content_text=row.content_text,
                classification=row.classification,
                score=self._score_chunk(
                    chunk_text=row.content_text,
                    query_text=query_text,
                    query_embedding=query_embedding,
                ),
            )
            for row in rows
        ]

        ranked_chunks = tuple(
            sorted(
                scored_chunks,
                key=lambda chunk: chunk.score,
                reverse=True,
            )[:top_k]
        )

        return RetrievalResult(chunks=ranked_chunks)

    async def _generate_query_embedding(
        self,
        *,
        tenant_context: TenantContext,
        query_text: str,
    ) -> list[float]:
        result = await self._ai_gateway_service.generate_embedding(
            EmbeddingRequest(
                tenant_context=tenant_context,
                model_name="text-embedding-3-small",
                input_text=query_text,
            )
        )
        return result.embedding

    def _build_statement(
        self,
        *,
        tenant_context: TenantContext,
        filters: RetrievalFilters,
    ) -> Select[tuple[DocumentChunk]]:
        statement = (
            select(DocumentChunk)
            .join(
                Document,
                Document.document_id == DocumentChunk.document_id,
            )
            .where(DocumentChunk.tenant_id == tenant_context.tenant_id)
            .where(Document.tenant_id == tenant_context.tenant_id)
            .where(Document.status == "active")
        )

        if filters.document_id is not None:
            statement = statement.where(DocumentChunk.document_id == filters.document_id)

        if filters.version is not None:
            statement = statement.where(DocumentChunk.version == filters.version)

        if filters.classification is not None:
            statement = statement.where(DocumentChunk.classification == filters.classification)

        return statement

    def _score_chunk(
        self,
        *,
        chunk_text: str,
        query_text: str,
        query_embedding: list[float],
    ) -> float:
        normalized_chunk = chunk_text.lower()
        normalized_query = query_text.strip().lower()

        lexical_bonus = 0.0
        if normalized_query and normalized_query in normalized_chunk:
            lexical_bonus = 0.2

        semantic_baseline = min(len(query_embedding) / 10, 1.0)

        return semantic_baseline + lexical_bonus