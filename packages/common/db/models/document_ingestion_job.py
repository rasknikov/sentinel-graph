from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from packages.common.db.base import Base


class DocumentIngestionJob(Base):
    __tablename__ = "document_ingestion_jobs"
    __table_args__ = (
        Index("ix_document_ingestion_jobs_tenant_id_status", "tenant_id", "status"),
        Index("ix_document_ingestion_jobs_tenant_id_document_id", "tenant_id", "document_id"),
    )

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("documents.document_id"),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.tenant_id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)