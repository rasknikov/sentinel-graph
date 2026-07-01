import pytest

from packages.common.errors import DomainError, ErrorCode
from packages.ingestion.contracts import (
    DocumentRecord,
    DocumentRegistrationRequest,
    DocumentStatus,
    DocumentVersionRecord,
)
from packages.ingestion.service import DocumentIngestionService
from packages.security.tenant_context import TenantContext


def build_tenant_context() -> TenantContext:
    return TenantContext(
        tenant_id="tenant_credit",
        user_id="user_123",
        roles=("analyst",),
        scopes=("documents:write",),
        department="credit",
        clearance_level="internal",
        session_id="session_abc",
        request_id="req_123",
        trace_id="trace_123",
        environment="test",
        auth_provider="https://identity.example.com",
    )


class FakeDocumentRepository:
    def __init__(self) -> None:
        self.created_record: DocumentRecord | None = None
        self.created_version_record: DocumentVersionRecord | None = None
        self.loaded_record: DocumentRecord | None = None
        self.loaded_version_record: DocumentVersionRecord | None = None
        self.activated_document: object | None = None
        self.activated_document_version: object | None = None

    async def create_document(
        self,
        record: DocumentRecord,
        version_record: DocumentVersionRecord,
    ) -> None:
        self.created_record = record
        self.created_version_record = version_record

    async def get_document_by_id_for_tenant(
        self,
        *,
        document_id: str,
        tenant_id: str,
    ) -> object | None:
        if self.loaded_record is None:
            return None

        class StoredDocument:
            def __init__(self, record: DocumentRecord) -> None:
                self.document_id = record.document_id
                self.tenant_id = record.tenant_id
                self.created_by = record.created_by
                self.title = record.title
                self.source_system = record.source_system
                self.content_hash = record.content_hash
                self.version = record.version
                self.classification = record.classification
                self.status = record.status.value

        if (
            self.loaded_record.document_id != document_id
            or self.loaded_record.tenant_id != tenant_id
        ):
            return None

        return StoredDocument(self.loaded_record)

    async def get_document_version_for_tenant(
        self,
        *,
        document_id: str,
        version: str,
        tenant_id: str,
    ) -> object | None:
        if self.loaded_version_record is None:
            return None

        class StoredDocumentVersion:
            def __init__(self, record: DocumentVersionRecord) -> None:
                self.document_id = record.document_id
                self.version = record.version
                self.tenant_id = record.tenant_id
                self.created_by = record.created_by
                self.content_text = record.content_text
                self.content_hash = record.content_hash
                self.classification = record.classification
                self.status = record.status.value

        if (
            self.loaded_version_record.document_id != document_id
            or self.loaded_version_record.version != version
            or self.loaded_version_record.tenant_id != tenant_id
        ):
            return None

        return StoredDocumentVersion(self.loaded_version_record)

    async def activate_document_version(
        self,
        *,
        document: object,
        document_version: object,
    ) -> None:
        document.version = document_version.version
        document.content_hash = document_version.content_hash
        document.classification = document_version.classification
        document.status = "active"
        document_version.status = "active"
        self.activated_document = document
        self.activated_document_version = document_version


@pytest.mark.asyncio
async def test_register_document_creates_draft_record_from_request_context() -> None:
    repository = FakeDocumentRepository()
    service = DocumentIngestionService(repository=repository)

    result = await service.register_document(
        DocumentRegistrationRequest(
            tenant_context=build_tenant_context(),
            document_id="doc_policy_v1",
            title="Credit Policy",
            source_system="sharepoint",
            content_text="Policy content",
            content_hash="hash_123",
            version="v1",
            classification="internal",
        )
    )

    assert repository.created_record is not None
    assert repository.created_version_record is not None
    assert repository.created_record.document_id == "doc_policy_v1"
    assert repository.created_version_record.version == "v1"
    assert repository.created_version_record.content_text == "Policy content"
    assert result.document_id == "doc_policy_v1"
    assert result.tenant_id == "tenant_credit"
    assert result.created_by == "user_123"
    assert result.title == "Credit Policy"
    assert result.source_system == "sharepoint"
    assert result.content_hash == "hash_123"
    assert result.version == "v1"
    assert result.classification == "internal"
    assert result.status is DocumentStatus.DRAFT


@pytest.mark.asyncio
async def test_get_document_returns_registered_document_for_current_tenant() -> None:
    repository = FakeDocumentRepository()
    repository.loaded_record = DocumentRecord(
        document_id="doc_policy_v1",
        tenant_id="tenant_credit",
        created_by="user_123",
        title="Credit Policy",
        source_system="sharepoint",
        content_hash="hash_123",
        version="v1",
        classification="internal",
        status=DocumentStatus.DRAFT,
    )
    service = DocumentIngestionService(repository=repository)

    result = await service.get_document(
        tenant_context=build_tenant_context(),
        document_id="doc_policy_v1",
    )

    assert result.document_id == "doc_policy_v1"
    assert result.tenant_id == "tenant_credit"
    assert result.created_by == "user_123"
    assert result.status is DocumentStatus.DRAFT


@pytest.mark.asyncio
async def test_get_document_raises_not_found_when_document_is_missing() -> None:
    service = DocumentIngestionService(repository=FakeDocumentRepository())

    with pytest.raises(DomainError) as exc_info:
        await service.get_document(
            tenant_context=build_tenant_context(),
            document_id="doc_missing",
        )

    assert exc_info.value.code is ErrorCode.DOCUMENT_NOT_FOUND
    assert exc_info.value.trace_id == "trace_123"


@pytest.mark.asyncio
async def test_activate_document_version_marks_document_as_active() -> None:
    repository = FakeDocumentRepository()
    repository.loaded_record = DocumentRecord(
        document_id="doc_policy_v1",
        tenant_id="tenant_credit",
        created_by="user_123",
        title="Credit Policy",
        source_system="sharepoint",
        content_hash="hash_123",
        version="v1",
        classification="internal",
        status=DocumentStatus.DRAFT,
    )
    repository.loaded_version_record = DocumentVersionRecord(
        document_id="doc_policy_v1",
        tenant_id="tenant_credit",
        created_by="user_123",
        version="v1",
        content_text="Policy content",
        content_hash="hash_123",
        classification="internal",
        status=DocumentStatus.DRAFT,
    )
    service = DocumentIngestionService(repository=repository)

    result = await service.activate_document_version(
        tenant_context=build_tenant_context(),
        document_id="doc_policy_v1",
        version="v1",
    )

    assert repository.activated_document is not None
    assert repository.activated_document_version is not None
    assert result.document_id == "doc_policy_v1"
    assert result.version == "v1"
    assert result.status is DocumentStatus.ACTIVE


@pytest.mark.asyncio
async def test_activate_document_version_raises_not_found_when_version_is_missing() -> None:
    repository = FakeDocumentRepository()
    repository.loaded_record = DocumentRecord(
        document_id="doc_policy_v1",
        tenant_id="tenant_credit",
        created_by="user_123",
        title="Credit Policy",
        source_system="sharepoint",
        content_hash="hash_123",
        version="v1",
        classification="internal",
        status=DocumentStatus.DRAFT,
    )
    service = DocumentIngestionService(repository=repository)

    with pytest.raises(DomainError) as exc_info:
        await service.activate_document_version(
            tenant_context=build_tenant_context(),
            document_id="doc_policy_v1",
            version="v2",
        )

    assert exc_info.value.code is ErrorCode.DOCUMENT_VERSION_NOT_FOUND
    assert exc_info.value.trace_id == "trace_123"
