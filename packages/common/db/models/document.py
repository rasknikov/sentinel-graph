from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from packages.common.db.base import Base


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_tenant_id_status", "tenant_id", "status"),
    )

    document_id: Mapped[str] = mapped_column(String(64), primary_key=True)
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
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_system: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    classification: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
