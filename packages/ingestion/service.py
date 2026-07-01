from packages.common.errors import DomainError, ErrorCode
from packages.common.ids import DocumentId, TenantId, UserId
from packages.ingestion.contracts import (
    DocumentRecord,
    DocumentRegistrationRequest,
    DocumentStatus,
    DocumentVersionRecord,
)
from packages.ingestion.repository import DocumentRepository
from packages.security.tenant_context import TenantContext


class DocumentIngestionService:
    def __init__(self, repository: DocumentRepository) -> None:
        self._repository = repository

    async def register_document(
        self,
        request: DocumentRegistrationRequest,
    ) -> DocumentRecord:
        document_record = DocumentRecord(
            document_id=DocumentId(request.document_id),
            tenant_id=TenantId(request.tenant_context.tenant_id),
            created_by=UserId(request.tenant_context.user_id),
            title=request.title,
            source_system=request.source_system,
            content_hash=request.content_hash,
            version=request.version,
            classification=request.classification,
            status=DocumentStatus.DRAFT,
        )
        version_record = DocumentVersionRecord(
            document_id=DocumentId(request.document_id),
            tenant_id=TenantId(request.tenant_context.tenant_id),
            created_by=UserId(request.tenant_context.user_id),
            version=request.version,
            content_text=request.content_text,
            content_hash=request.content_hash,
            classification=request.classification,
            status=DocumentStatus.DRAFT,
        )

        await self._repository.create_document(document_record, version_record)

        return document_record

    async def get_document(
        self,
        *,
        tenant_context: TenantContext,
        document_id: str,
    ) -> DocumentRecord:
        document = await self._repository.get_document_by_id_for_tenant(
            document_id=document_id,
            tenant_id=tenant_context.tenant_id,
        )

        if document is None:
            raise DomainError(
                code=ErrorCode.DOCUMENT_NOT_FOUND,
                message="Document was not found for the current tenant.",
                trace_id=tenant_context.trace_id,
            )

        return DocumentRecord(
            document_id=DocumentId(document.document_id),
            tenant_id=TenantId(document.tenant_id),
            created_by=UserId(document.created_by),
            title=document.title,
            source_system=document.source_system,
            content_hash=document.content_hash,
            version=document.version,
            classification=document.classification,
            status=DocumentStatus(document.status),
        )

    async def activate_document_version(
        self,
        *,
        tenant_context: TenantContext,
        document_id: str,
        version: str,
    ) -> DocumentRecord:
        document = await self._repository.get_document_by_id_for_tenant(
            document_id=document_id,
            tenant_id=tenant_context.tenant_id,
        )
        if document is None:
            raise DomainError(
                code=ErrorCode.DOCUMENT_NOT_FOUND,
                message="Document was not found for the current tenant.",
                trace_id=tenant_context.trace_id,
            )

        document_version = await self._repository.get_document_version_for_tenant(
            document_id=document_id,
            version=version,
            tenant_id=tenant_context.tenant_id,
        )
        if document_version is None:
            raise DomainError(
                code=ErrorCode.DOCUMENT_VERSION_NOT_FOUND,
                message="Document version was not found for the current tenant.",
                trace_id=tenant_context.trace_id,
            )

        await self._repository.activate_document_version(
            document=document,
            document_version=document_version,
        )

        return DocumentRecord(
            document_id=DocumentId(document.document_id),
            tenant_id=TenantId(document.tenant_id),
            created_by=UserId(document.created_by),
            title=document.title,
            source_system=document.source_system,
            content_hash=document.content_hash,
            version=document.version,
            classification=document.classification,
            status=DocumentStatus(document.status),
        )
