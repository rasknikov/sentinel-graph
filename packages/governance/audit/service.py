from sqlalchemy.ext.asyncio import AsyncSession

from packages.governance.audit.contracts import AuditEventWrite, AuditRecordRef
from packages.governance.audit.repository import AuditRepository


class AuditService:
    def __init__(self, repository: AuditRepository | None = None) -> None:
        self.repository = repository or AuditRepository()

    async def record_event(
            self,
            session: AsyncSession,
            event: AuditEventWrite,
    ) -> AuditRecordRef:
        return await self.repository.create(
            session=session,
            event=event,
        )