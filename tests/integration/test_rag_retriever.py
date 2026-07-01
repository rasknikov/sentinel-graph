from datetime import UTC, datetime

import pytest

from packages.common.db.models.document import Document
from packages.common.db.models.document_chunk import DocumentChunk
from packages.common.db.models.tenant import Tenant
from packages.common.db.models.user import User
from packages.rag.contracts import RetrievalFilters
from packages.rag.retriever import DocumentChunkRetriever
from packages.security.tenant_context import TenantContext


def build_tenant_context() -> TenantContext:
    return TenantContext(
        tenant_id="tenant_credit",
        user_id="user_123",
        roles=("analyst",),
        scopes=("rag:query",),
        department="credit",
        clearance_level="internal",
        session_id="session_abc",
        request_id="req_123",
        trace_id="trace_123",
        environment="test",
        auth_provider="https://identity.example.com",
    )


async def seed_retrieval_records(db_session) -> None:
    now = datetime.now(UTC)

    db_session.add(
        Tenant(
            tenant_id="tenant_credit",
            name="Credit Risk",
            status="active",
            description="Credit tenant",
            created_at=now,
            updated_at=now,
        )
    )
    db_session.add(
        Tenant(
            tenant_id="tenant_compliance",
            name="Compliance",
            status="active",
            description="Compliance tenant",
            created_at=now,
            updated_at=now,
        )
    )
    db_session.add(
        User(
            user_id="user_123",
            email="analyst@example.com",
            department="credit",
            clearance_level="internal",
            status="active",
            created_at=now,
            updated_at=now,
        )
    )
    db_session.add(
        Document(
            document_id="doc_policy_active",
            tenant_id="tenant_credit",
            created_by="user_123",
            title="Active Credit Policy",
            source_system="sharepoint",
            version="v1",
            content_hash="hash_active",
            classification="internal",
            status="active",
            created_at=now,
            updated_at=now,
        )
    )
    db_session.add(
        Document(
            document_id="doc_policy_draft",
            tenant_id="tenant_credit",
            created_by="user_123",
            title="Draft Credit Policy",
            source_system="sharepoint",
            version="v1",
            content_hash="hash_draft",
            classification="internal",
            status="draft",
            created_at=now,
            updated_at=now,
        )
    )
    db_session.add(
        Document(
            document_id="doc_policy_other_tenant",
            tenant_id="tenant_compliance",
            created_by="user_123",
            title="Compliance Policy",
            source_system="sharepoint",
            version="v1",
            content_hash="hash_other",
            classification="restricted",
            status="active",
            created_at=now,
            updated_at=now,
        )
    )
    db_session.add(
        DocumentChunk(
            chunk_id="chunk_credit_1",
            document_id="doc_policy_active",
            version="v1",
            tenant_id="tenant_credit",
            chunk_index=0,
            content_text="Credit approval policy for analysts.",
            content_hash="chunk_hash_credit_1",
            classification="internal",
            chunking_strategy_version="chunker_v1",
            created_at=now,
        )
    )
    db_session.add(
        DocumentChunk(
            chunk_id="chunk_credit_2",
            document_id="doc_policy_draft",
            version="v1",
            tenant_id="tenant_credit",
            chunk_index=0,
            content_text="Draft policy that should not be retrieved.",
            content_hash="chunk_hash_credit_2",
            classification="internal",
            chunking_strategy_version="chunker_v1",
            created_at=now,
        )
    )
    db_session.add(
        DocumentChunk(
            chunk_id="chunk_compliance_1",
            document_id="doc_policy_other_tenant",
            version="v1",
            tenant_id="tenant_compliance",
            chunk_index=0,
            content_text="Compliance policy content.",
            content_hash="chunk_hash_compliance_1",
            classification="restricted",
            chunking_strategy_version="chunker_v1",
            created_at=now,
        )
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_retriever_returns_active_chunks_for_current_tenant(db_session) -> None:
    await seed_retrieval_records(db_session)
    retriever = DocumentChunkRetriever(session=db_session)

    result = await retriever.search(
        tenant_context=build_tenant_context(),
        query_text="credit policy",
        top_k=5,
        filters=RetrievalFilters(),
    )

    assert len(result.chunks) == 1
    assert result.chunks[0].chunk_id == "chunk_credit_1"
    assert result.chunks[0].tenant_id == "tenant_credit"
    assert result.chunks[0].document_id == "doc_policy_active"


@pytest.mark.asyncio
async def test_retriever_excludes_chunks_from_other_tenants(db_session) -> None:
    await seed_retrieval_records(db_session)
    retriever = DocumentChunkRetriever(session=db_session)

    result = await retriever.search(
        tenant_context=build_tenant_context(),
        query_text="compliance policy",
        top_k=5,
        filters=RetrievalFilters(),
    )

    chunk_ids = {chunk.chunk_id for chunk in result.chunks}

    assert "chunk_compliance_1" not in chunk_ids
    assert all(chunk.tenant_id == "tenant_credit" for chunk in result.chunks)


@pytest.mark.asyncio
async def test_retriever_excludes_inactive_documents(db_session) -> None:
    await seed_retrieval_records(db_session)
    retriever = DocumentChunkRetriever(session=db_session)

    result = await retriever.search(
        tenant_context=build_tenant_context(),
        query_text="draft policy",
        top_k=5,
        filters=RetrievalFilters(),
    )

    chunk_ids = {chunk.chunk_id for chunk in result.chunks}

    assert "chunk_credit_2" not in chunk_ids


@pytest.mark.asyncio
async def test_retriever_respects_document_id_version_and_classification_filters(db_session) -> None:
    await seed_retrieval_records(db_session)
    retriever = DocumentChunkRetriever(session=db_session)

    result = await retriever.search(
        tenant_context=build_tenant_context(),
        query_text="credit policy",
        top_k=5,
        filters=RetrievalFilters(
            document_id="doc_policy_active",
            version="v1",
            classification="internal",
        ),
    )

    assert len(result.chunks) == 1
    assert result.chunks[0].document_id == "doc_policy_active"
    assert result.chunks[0].version == "v1"
    assert result.chunks[0].classification == "internal"
