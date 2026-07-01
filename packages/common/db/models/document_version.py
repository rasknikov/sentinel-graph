from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.common.db.base import Base


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        Index("ix_document_versions_tenant_id_status", "tenant_id", "status"),
        Index("ix_document_versions_tenant_id_document_id", "tenant_id", "document_id"),
    )

    document_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("documents.document_id"),
        primary_key=True,
    )
    version: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.tenant_id"),
        nullable=False,
    )
    created_by: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    classification: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
