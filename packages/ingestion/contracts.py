from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from packages.common.ids import TenantId, UserId
from packages.security.tenant_context import TenantContext


class DocumentStatus(StrEnum):
    DRAFT = "draft"
    INGESTING = "ingesting"
    ACTIVE = "active"
    FAILED = "failed"
    ARCHIVED = "archived"


class DocumentRegistrationRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_context: TenantContext
    document_id: str
    title: str
    source_system: str
    content_text: str
    content_hash: str
    version: str
    classification: str


class DocumentRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_id: str
    tenant_id: TenantId
    created_by: UserId
    title: str
    source_system: str
    content_hash: str
    version: str
    classification: str
    status: DocumentStatus


class DocumentVersionRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_id: str
    tenant_id: TenantId
    created_by: UserId
    version: str
    content_text: str
    content_hash: str
    classification: str
    status: DocumentStatus


class IngestionJobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentChunkRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk_id: str
    document_id: str
    tenant_id: TenantId
    version: str
    chunk_index: int
    content_text: str
    content_hash: str
    classification: str
    chunking_strategy_version: str


class DocumentIngestionJobRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    job_id: str
    document_id: str
    tenant_id: TenantId
    version: str
    status: IngestionJobStatus

class EmbeddedChunkRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk_id: str
    embedding_model_name: str
    embedding_vector: list[float]