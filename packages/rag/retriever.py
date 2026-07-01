from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.db.models import Document, DocumentChunk
from packages.rag.contracts import RetrievedChunk, RetrievalFilters, RetrievalResult
from packages.security.tenant_context import TenantContext


class DocumentChunkRetriever:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(
        self,
        *,
        tenant_context: TenantContext,
        query_text: str,
        top_k: int,
        filters: RetrievalFilters,
    ) -> RetrievalResult:
        statement = self._build_statement(
            tenant_context=tenant_context,
            filters=filters,
        ).limit(top_k)

        result = await self._session.execute(statement)
        rows = result.scalars().all()

        normalized_query = query_text.strip().lower()

        chunks = tuple(
            RetrievedChunk(
                chunk_id=row.chunk_id,
                document_id=row.document_id,
                version=row.version,
                tenant_id=row.tenant_id,
                content_text=row.content_text,
                classification=row.classification,
                score=self._score_chunk(
                    chunk_text=row.content_text,
                    normalized_query=normalized_query,
                ),
            )
            for row in rows
        )

        return RetrievalResult(chunks=chunks)

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

        return statement.order_by(DocumentChunk.chunk_index.asc())

    def _score_chunk(
        self,
        *,
        chunk_text: str,
        normalized_query: str,
    ) -> float:
        if not normalized_query:
            return 0.0

        normalized_chunk = chunk_text.lower()

        if normalized_query in normalized_chunk:
            return 1.0

        query_terms = [term for term in normalized_query.split() if term]
        if not query_terms:
            return 0.0

        matched_terms = sum(1 for term in query_terms if term in normalized_chunk)
        return matched_terms / len(query_terms)
