from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from apps.api.main import app
from packages.ai_gateway.contracts import EmbeddingRequest, EmbeddingResult
from packages.ai_gateway.dependencies import get_ai_gateway_service
from packages.common.db.dependencies import get_db_session
from packages.common.db.models.document import Document
from packages.common.db.models.document_version import DocumentVersion
from packages.common.db.models.tenant import Tenant
from packages.common.db.models.user import User
from packages.ingestion.contracts import (
    DocumentRecord,
    DocumentRegistrationRequest,
    DocumentStatus,
)
from packages.ingestion.dependencies import get_document_ingestion_service
from tests.integration.test_health_route import build_auth_header


class FakeDocumentIngestionService:
    def __init__(self) -> None:
        self.last_request: DocumentRegistrationRequest | None = None

    async def register_document(
        self,
        request: DocumentRegistrationRequest,
    ) -> DocumentRecord:
        self.last_request = request
        return DocumentRecord(
            document_id=request.document_id,
            tenant_id=request.tenant_context.tenant_id,
            created_by=request.tenant_context.user_id,
            title=request.title,
            source_system=request.source_system,
            content_hash=request.content_hash,
            version=request.version,
            classification=request.classification,
            status=DocumentStatus.DRAFT,
        )


class FakeEmbeddingGatewayService:
    async def generate_embedding(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResult:
        return EmbeddingResult(
            model_name=request.model_name,
            embedding=[0.1, 0.2, 0.3],
        )


def build_db_session_override(db_session):
    async def _override_db_session():
        yield db_session

    return _override_db_session


async def seed_document_dependencies(db_session) -> None:
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
    await db_session.commit()


@pytest.mark.asyncio
async def test_documents_route_requires_authentication() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/v1/documents",
            json={
                "document_id": "doc_policy_v1",
                "title": "Credit Policy",
                "source_system": "sharepoint",
                "content_text": "Policy content",
                "content_hash": "hash_123",
                "version": "v1",
                "classification": "internal",
            },
        )

    payload = response.json()

    assert response.status_code == 401
    assert payload["code"] == "authentication_required"
    assert payload["message"] == "Authentication is required."
    assert payload["trace_id"].startswith("trace_")


@pytest.mark.asyncio
async def test_documents_route_registers_document_for_current_tenant() -> None:
    fake_service = FakeDocumentIngestionService()
    app.dependency_overrides[get_document_ingestion_service] = lambda: fake_service
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/v1/documents",
                headers=build_auth_header(),
                json={
                    "document_id": "doc_policy_v1",
                    "title": "Credit Policy",
                    "source_system": "sharepoint",
                    "content_text": "Policy content",
                    "content_hash": "hash_123",
                    "version": "v1",
                    "classification": "internal",
                },
            )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()

    assert response.status_code == 200
    assert payload == {
        "document_id": "doc_policy_v1",
        "status": "draft",
    }
    assert fake_service.last_request is not None
    assert fake_service.last_request.tenant_context.tenant_id == "tenant_credit"
    assert fake_service.last_request.tenant_context.user_id == "user_123"


@pytest.mark.asyncio
async def test_documents_route_persists_document_in_database(db_session) -> None:
    await seed_document_dependencies(db_session)
    app.dependency_overrides[get_db_session] = build_db_session_override(db_session)
    app.dependency_overrides[get_ai_gateway_service] = lambda: FakeEmbeddingGatewayService()
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/v1/documents",
                headers=build_auth_header(),
                json={
                    "document_id": "doc_policy_v1",
                    "title": "Credit Policy",
                    "source_system": "sharepoint",
                    "content_text": "Policy content",
                    "content_hash": "hash_123",
                    "version": "v1",
                    "classification": "internal",
                },
            )
    finally:
        app.dependency_overrides.clear()

    result = await db_session.execute(
        select(Document).where(Document.document_id == "doc_policy_v1")
    )
    stored = result.scalar_one()
    version_result = await db_session.execute(
        select(DocumentVersion).where(
            DocumentVersion.document_id == "doc_policy_v1",
            DocumentVersion.version == "v1",
        )
    )
    stored_version = version_result.scalar_one()

    assert response.status_code == 200
    assert stored.tenant_id == "tenant_credit"
    assert stored.created_by == "user_123"
    assert stored.title == "Credit Policy"
    assert stored.status == "draft"
    assert stored_version.tenant_id == "tenant_credit"
    assert stored_version.created_by == "user_123"
    assert stored_version.content_text == "Policy content"
    assert stored_version.content_hash == "hash_123"
    assert stored_version.status == "draft"


@pytest.mark.asyncio
async def test_documents_route_allows_registering_new_version_for_existing_document(db_session) -> None:
    await seed_document_dependencies(db_session)
    app.dependency_overrides[get_db_session] = build_db_session_override(db_session)
    app.dependency_overrides[get_ai_gateway_service] = lambda: FakeEmbeddingGatewayService()
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            first_response = await client.post(
                "/v1/documents",
                headers=build_auth_header(),
                json={
                    "document_id": "doc_policy_v1",
                    "title": "Credit Policy",
                    "source_system": "sharepoint",
                    "content_text": "Policy content v1",
                    "content_hash": "hash_v1",
                    "version": "v1",
                    "classification": "internal",
                },
            )
            second_response = await client.post(
                "/v1/documents",
                headers=build_auth_header(),
                json={
                    "document_id": "doc_policy_v1",
                    "title": "Credit Policy Updated",
                    "source_system": "sharepoint",
                    "content_text": "Policy content v2",
                    "content_hash": "hash_v2",
                    "version": "v2",
                    "classification": "internal",
                },
            )
    finally:
        app.dependency_overrides.clear()

    document_result = await db_session.execute(
        select(Document).where(Document.document_id == "doc_policy_v1")
    )
    stored_document = document_result.scalar_one()
    version_result = await db_session.execute(
        select(DocumentVersion).where(DocumentVersion.document_id == "doc_policy_v1")
    )
    stored_versions = version_result.scalars().all()

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert stored_document.title == "Credit Policy Updated"
    assert stored_document.version == "v2"
    assert stored_document.status == "draft"
    assert {version.version for version in stored_versions} == {"v1", "v2"}


@pytest.mark.asyncio
async def test_get_document_route_returns_document_for_current_tenant(db_session) -> None:
    await seed_document_dependencies(db_session)
    app.dependency_overrides[get_db_session] = build_db_session_override(db_session)
    app.dependency_overrides[get_ai_gateway_service] = lambda: FakeEmbeddingGatewayService()
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            create_response = await client.post(
                "/v1/documents",
                headers=build_auth_header(),
                json={
                    "document_id": "doc_policy_v1",
                    "title": "Credit Policy",
                    "source_system": "sharepoint",
                    "content_text": "Policy content",
                    "content_hash": "hash_123",
                    "version": "v1",
                    "classification": "internal",
                },
            )
            get_response = await client.get(
                "/v1/documents/doc_policy_v1",
                headers=build_auth_header(),
            )
    finally:
        app.dependency_overrides.clear()

    assert create_response.status_code == 200
    assert get_response.status_code == 200
    assert get_response.json() == {
        "document_id": "doc_policy_v1",
        "tenant_id": "tenant_credit",
        "created_by": "user_123",
        "title": "Credit Policy",
        "source_system": "sharepoint",
        "content_hash": "hash_123",
        "version": "v1",
        "classification": "internal",
        "status": "draft",
    }


@pytest.mark.asyncio
async def test_activate_document_version_route_marks_version_as_active(db_session) -> None:
    await seed_document_dependencies(db_session)
    app.dependency_overrides[get_db_session] = build_db_session_override(db_session)
    app.dependency_overrides[get_ai_gateway_service] = lambda: FakeEmbeddingGatewayService()
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            create_response = await client.post(
                "/v1/documents",
                headers=build_auth_header(),
                json={
                    "document_id": "doc_policy_v1",
                    "title": "Credit Policy",
                    "source_system": "sharepoint",
                    "content_text": "Policy content",
                    "content_hash": "hash_123",
                    "version": "v1",
                    "classification": "internal",
                },
            )
            activate_response = await client.post(
                "/v1/documents/doc_policy_v1/versions/v1/activate",
                headers=build_auth_header(),
            )
    finally:
        app.dependency_overrides.clear()

    document_result = await db_session.execute(
        select(Document).where(Document.document_id == "doc_policy_v1")
    )
    stored_document = document_result.scalar_one()
    version_result = await db_session.execute(
        select(DocumentVersion).where(
            DocumentVersion.document_id == "doc_policy_v1",
            DocumentVersion.version == "v1",
        )
    )
    stored_version = version_result.scalar_one()

    assert create_response.status_code == 200
    assert activate_response.status_code == 200
    assert activate_response.json() == {
        "document_id": "doc_policy_v1",
        "version": "v1",
        "status": "active",
    }
    assert stored_document.status == "active"
    assert stored_document.version == "v1"
    assert stored_version.status == "active"


@pytest.mark.asyncio
async def test_activate_document_version_route_returns_not_found_for_missing_version(db_session) -> None:
    await seed_document_dependencies(db_session)
    app.dependency_overrides[get_db_session] = build_db_session_override(db_session)
    app.dependency_overrides[get_ai_gateway_service] = lambda: FakeEmbeddingGatewayService()
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            create_response = await client.post(
                "/v1/documents",
                headers=build_auth_header(),
                json={
                    "document_id": "doc_policy_v1",
                    "title": "Credit Policy",
                    "source_system": "sharepoint",
                    "content_text": "Policy content",
                    "content_hash": "hash_123",
                    "version": "v1",
                    "classification": "internal",
                },
            )
            activate_response = await client.post(
                "/v1/documents/doc_policy_v1/versions/v2/activate",
                headers=build_auth_header(),
            )
    finally:
        app.dependency_overrides.clear()

    assert create_response.status_code == 200
    assert activate_response.status_code == 404
    payload = activate_response.json()

    assert payload["error"]["code"] == "DOCUMENT_VERSION_NOT_FOUND"
    assert payload["error"]["message"] == "Document version was not found for the current tenant."
    assert payload["error"]["trace_id"].startswith("trace_")


@pytest.mark.asyncio
async def test_get_document_route_returns_not_found_for_missing_document(db_session) -> None:
    await seed_document_dependencies(db_session)
    app.dependency_overrides[get_db_session] = build_db_session_override(db_session)
    app.dependency_overrides[get_ai_gateway_service] = lambda: FakeEmbeddingGatewayService()
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get(
                "/v1/documents/doc_missing",
                headers=build_auth_header(),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    payload = response.json()

    assert payload["error"]["code"] == "DOCUMENT_NOT_FOUND"
    assert payload["error"]["message"] == "Document was not found for the current tenant."
    assert payload["error"]["trace_id"].startswith("trace_")
