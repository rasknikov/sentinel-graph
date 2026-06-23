from typing import Final, NewType

TenantId = NewType("TenantId", str)
UserId = NewType("UserId", str)
SessionId = NewType("SessionId", str)
RequestId = NewType("RequestId", str)
TraceId = NewType("TraceId", str)
DocumentId = NewType("DocumentId", str)
ChunkId = NewType("ChunkId", str)
PromptId = NewType("PromptId", str)
ModelId = NewType("ModelId", str)
ToolId = NewType("ToolId", str)
PolicyId = NewType("PolicyId", str)
AuditId = NewType("AuditId", str)

CORE_ID_TYPES: Final[tuple[str, ...]] = (
    "TenantId",
    "UserId",
    "SessionId",
    "RequestId",
    "TraceId",
    "DocumentId",
    "ChunkId",
    "PromptId",
    "ModelId",
    "ToolId",
    "PolicyId",
    "AuditId",
)
