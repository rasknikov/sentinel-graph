from pydantic import BaseModel, ConfigDict
from fastapi import APIRouter, Depends

from packages.ingestion.contracts import DocumentRegistrationRequest
from packages.ingestion.dependencies import get_document_ingestion_service
from packages.ingestion.service import DocumentIngestionService
from packages.security.dependencies import require_tenant_context
from packages.security.tenant_context import TenantContext


router = APIRouter(tags=["documents"])


class CreateDocumentPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_id: str
    title: str
    source_system: str
    content_text: str
    content_hash: str
    version: str
    classification: str


@router.post("/v1/documents")
async def create_document(
    payload: CreateDocumentPayload,
    tenant_context: TenantContext = Depends(require_tenant_context),
    ingestion_service: DocumentIngestionService = Depends(get_document_ingestion_service),
) -> dict[str, str]:
    result = await ingestion_service.register_document(
        DocumentRegistrationRequest(
            tenant_context=tenant_context,
            document_id=payload.document_id,
            title=payload.title,
            source_system=payload.source_system,
            content_text=payload.content_text,
            content_hash=payload.content_hash,
            version=payload.version,
            classification=payload.classification,
        )
    )

    return {
        "document_id": result.document_id,
        "status": result.status.value,
    }


@router.get("/v1/documents/{document_id}")
async def get_document(
    document_id: str,
    tenant_context: TenantContext = Depends(require_tenant_context),
    ingestion_service: DocumentIngestionService = Depends(get_document_ingestion_service),
) -> dict[str, str]:
    result = await ingestion_service.get_document(
        tenant_context=tenant_context,
        document_id=document_id,
    )

    return {
        "document_id": result.document_id,
        "tenant_id": result.tenant_id,
        "created_by": result.created_by,
        "title": result.title,
        "source_system": result.source_system,
        "content_hash": result.content_hash,
        "version": result.version,
        "classification": result.classification,
        "status": result.status.value,
    }


@router.post("/v1/documents/{document_id}/versions/{version}/activate")
async def activate_document_version(
    document_id: str,
    version: str,
    tenant_context: TenantContext = Depends(require_tenant_context),
    ingestion_service: DocumentIngestionService = Depends(get_document_ingestion_service),
) -> dict[str, str]:
    result = await ingestion_service.activate_document_version(
        tenant_context=tenant_context,
        document_id=document_id,
        version=version,
    )

    return {
        "document_id": result.document_id,
        "version": result.version,
        "status": result.status.value,
    }
