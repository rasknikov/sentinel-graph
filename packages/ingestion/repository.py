from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.db.models import (
    Document,
    DocumentChunk,
    DocumentIngestionJob,
    DocumentVersion,
)
from packages.ingestion.contracts import (
    DocumentChunkRecord,
    DocumentIngestionJobRecord,
    DocumentRecord,
    DocumentVersionRecord,
)


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_document(
        self,
        record: DocumentRecord,
        version_record: DocumentVersionRecord,
    ) -> Document:
        now = datetime.now(UTC).replace(tzinfo=None)
        document = await self.get_document_by_id_for_tenant(
            document_id=record.document_id,
            tenant_id=record.tenant_id,
        )

        if document is None:
            document = Document(
                document_id=record.document_id,
                tenant_id=record.tenant_id,
                created_by=record.created_by,
                title=record.title,
                source_system=record.source_system,
                version=record.version,
                content_hash=record.content_hash,
                classification=record.classification,
                status=record.status.value,
                created_at=now,
                updated_at=None,
            )
            self._session.add(document)
        else:
            document.title = record.title
            document.source_system = record.source_system
            document.updated_at = now

            if document.status != "active":
                document.version = record.version
                document.content_hash = record.content_hash
                document.classification = record.classification
                document.status = record.status.value

        document_version = DocumentVersion(
            document_id=version_record.document_id,
            version=version_record.version,
            tenant_id=version_record.tenant_id,
            created_by=version_record.created_by,
            content_text=version_record.content_text,
            content_hash=version_record.content_hash,
            classification=version_record.classification,
            status=version_record.status.value,
            created_at=now,
            updated_at=None,
        )

        self._session.add(document_version)
        await self._session.flush()

        return document

    async def create_chunks(
        self,
        chunks: list[DocumentChunkRecord],
    ) -> None:
        now = datetime.now(UTC).replace(tzinfo=None)

        for chunk in chunks:
            self._session.add(
                DocumentChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    version=chunk.version,
                    tenant_id=chunk.tenant_id,
                    chunk_index=chunk.chunk_index,
                    content_text=chunk.content_text,
                    content_hash=chunk.content_hash,
                    classification=chunk.classification,
                    chunking_strategy_version=chunk.chunking_strategy_version,
                    created_at=now,
                )
            )

        await self._session.flush()

    async def create_ingestion_job(
        self,
        job: DocumentIngestionJobRecord,
    ) -> None:
        now = datetime.now(UTC).replace(tzinfo=None)

        self._session.add(
            DocumentIngestionJob(
                job_id=job.job_id,
                document_id=job.document_id,
                version=job.version,
                tenant_id=job.tenant_id,
                status=job.status.value,
                created_at=now,
                updated_at=None,
            )
        )
        await self._session.flush()

    async def update_ingestion_job(
        self,
        job: DocumentIngestionJobRecord,
    ) -> None:
        stored_job = await self.get_ingestion_job_by_id(job.job_id)

        if stored_job is None:
            return

        stored_job.status = job.status.value
        stored_job.updated_at = datetime.now(UTC).replace(tzinfo=None)
        await self._session.flush()

    async def get_ingestion_job_by_id(
        self,
        job_id: str,
    ) -> DocumentIngestionJob | None:
        result = await self._session.execute(
            select(DocumentIngestionJob).where(
                DocumentIngestionJob.job_id == job_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_document_by_id_for_tenant(
        self,
        *,
        document_id: str,
        tenant_id: str,
    ) -> Document | None:
        result = await self._session.execute(
            select(Document).where(
                Document.document_id == document_id,
                Document.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_document_version_for_tenant(
        self,
        *,
        document_id: str,
        version: str,
        tenant_id: str,
    ) -> DocumentVersion | None:
        result = await self._session.execute(
            select(DocumentVersion).where(
                DocumentVersion.document_id == document_id,
                DocumentVersion.version == version,
                DocumentVersion.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def activate_document_version(
        self,
        *,
        document: Document,
        document_version: DocumentVersion,
    ) -> None:
        now = datetime.now(UTC).replace(tzinfo=None)
        document.version = document_version.version
        document.content_hash = document_version.content_hash
        document.classification = document_version.classification
        document.status = "active"
        document.updated_at = now

        document_version.status = "active"
        document_version.updated_at = now

        await self._session.flush()