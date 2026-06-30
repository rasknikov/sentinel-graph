from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.ids import AuditId
from packages.common.db.models.audit_event import AuditEvent
from packages.governance.audit.contracts import AuditEventWrite, AuditRecordRef


class AuditRepository:
    async def create(
            self,
            session: AsyncSession,
            event: AuditEventWrite,
    ) -> AuditRecordRef:
        audit_id = AuditId(f"audit_{uuid4().hex}")

        record = AuditEvent(
            event_id=audit_id,
            tenant_id=event.tenant_id,
            user_id=event.user_id,
            request_id=event.request_id,
            trace_id=event.trace_id,
            event_type=event.event_type,
            message=event.message,
            created_at=datetime.now(UTC),
        )

        session.add(record)
        await session.commit()

        return AuditRecordRef(
            audit_id=audit_id,
            tenant_id=event.tenant_id,
            user_id=event.user_id,
            request_id=event.request_id,
            trace_id=event.trace_id,
            event_type=event.event_type,
            error_code=event.error_code,
        )