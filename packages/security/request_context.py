from uuid import uuid4

from packages.common.ids import RequestId, TraceId


def generate_request_id() -> RequestId:
    return RequestId(f"req_{uuid4().hex}")


def generate_trace_id() -> TraceId:
    return TraceId(f"trace_{uuid4().hex}")