from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from packages.common.db.models.tenant import Tenant


@pytest.mark.asyncio
async def test_can_persist_and_load_tenant(db_session) -> None:
    tenant = Tenant(
        tenant_id="tenant_credit",
        name="Credit Risk",
        status="active",
        description="Credit tenant",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    db_session.add(tenant)
    await db_session.commit()

    result = await db_session.execute(
        select(Tenant).where(Tenant.tenant_id == "tenant_credit")
    )
    loaded_tenant = result.scalar_one()

    assert loaded_tenant.tenant_id == "tenant_credit"
    assert loaded_tenant.name == "Credit Risk"
