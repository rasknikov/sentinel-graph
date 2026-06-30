from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from packages.common.db.models.audit_event import AuditEvent
from packages.common.db.models.request import Request
from packages.common.db.models.session import Session
from packages.common.db.models.tenant import Tenant
from packages.common.db.models.user import User
from packages.common.errors import ErrorCode
from packages.governance.audit.contracts import AuditEventWrite
from packages.governance.audit.repository import AuditRepository
from packages.governance.audit.service import AuditService


async def seed_security_records(db_session) -> None:
    now = datetime.now(UTC)

    db_session.add(
        Tenant(
            tenant_id="tenant_credit",
            name="Credit Risk",
            status="active",
            description="Credit tenant",
            created_at=now,
            updated_at=now,
        )
    )
    db_session.add(
        User(
            user_id="user_123",
            email="analyst@example.com",
            department="credit",
            clearance_level="internal",
            status="active",
            created_at=now,
            updated_at=now,
        )
    )
    db_session.add(
        Session(
            session_id="session_abc",
            tenant_id="tenant_credit",
            user_id="user_123",
            status="active",
            created_at=now,
            updated_at=now,
        )
    )
    db_session.add(
        Request(
            request_id="req_123",
            tenant_id="tenant_credit",
            user_id="user_123",
            session_id="session_abc",
            trace_id="trace_123",
            status="accepted",
            input_text="GET /me/policy-check",
            created_at=now,
            updated_at=now,
            completed_at=None,
        )
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_audit_repository_persists_event(db_session) -> None:
    await seed_security_records(db_session)
    repository = AuditRepository()

    record_ref = await repository.create(
        session=db_session,
        event=AuditEventWrite(
            tenant_id="tenant_credit",
            user_id="user_123",
            request_id="req_123",
            trace_id="trace_123",
            event_type="policy_check",
            message="Policy check passed.",
            error_code=None,
        ),
    )

    result = await db_session.execute(
        select(AuditEvent).where(AuditEvent.event_id == record_ref.audit_id)
    )
    stored = result.scalar_one()

    assert record_ref.event_type == "policy_check"
    assert stored.trace_id == "trace_123"
    assert stored.message == "Policy check passed."


@pytest.mark.asyncio
async def test_audit_service_records_event(db_session) -> None:
    await seed_security_records(db_session)
    service = AuditService()

    record_ref = await service.record_event(
        session=db_session,
        event=AuditEventWrite(
            tenant_id="tenant_credit",
            user_id="user_123",
            request_id="req_123",
            trace_id="trace_123",
            event_type="policy_denied",
            message="Required scope is missing.",
            error_code=ErrorCode.TENANT_ACCESS_DENIED,
        ),
    )

    result = await db_session.execute(
        select(AuditEvent).where(AuditEvent.event_id == record_ref.audit_id)
    )
    stored = result.scalar_one()

    assert record_ref.error_code is ErrorCode.TENANT_ACCESS_DENIED
    assert stored.event_type == "policy_denied"
    assert stored.message == "Required scope is missing."
