from sqlalchemy.sql.schema import MetaData

from packages.common.db.base import Base
from packages.common.db.models import (
    AuditEvent,
    Document,
    DocumentChunk,
    DocumentIngestionJob,
    DocumentVersion,
    Request,
    Session,
    Tenant,
    User,
)


def get_metadata() -> MetaData:
    return Base.metadata


__all__ = [
    "AuditEvent",
    "Document",
    "DocumentChunk",
    "DocumentIngestionJob",
    "DocumentVersion",
    "Request",
    "Session",
    "Tenant",
    "User",
    "get_metadata",
]