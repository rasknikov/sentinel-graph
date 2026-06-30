from packages.governance.audit.service import AuditService


def get_audit_service() -> AuditService:
    return AuditService()