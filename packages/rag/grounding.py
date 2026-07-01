from packages.common.errors import DomainError, ErrorCode
from packages.rag.citations import Citation


def validate_grounding(
    *,
    answer_text: str,
    citations: tuple[Citation, ...],
    trace_id: str,
) -> None:
    if not answer_text.strip():
        raise DomainError(
            code=ErrorCode.GROUNDING_FAILED,
            message="Grounded answer is empty.",
            trace_id=trace_id,
        )

    if not citations:
        raise DomainError(
            code=ErrorCode.GROUNDING_FAILED,
            message="Grounded answer requires citations.",
            trace_id=trace_id,
        )

    for citation in citations:
        if not citation.document_id.strip():
            raise DomainError(
                code=ErrorCode.GROUNDING_FAILED,
                message="Citation requires document_id.",
                trace_id=trace_id,
            )

        if not citation.document_version.strip():
            raise DomainError(
                code=ErrorCode.GROUNDING_FAILED,
                message="Citation requires document_version.",
                trace_id=trace_id,
            )

        if not citation.chunk_id.strip():
            raise DomainError(
                code=ErrorCode.GROUNDING_FAILED,
                message="Citation requires chunk_id.",
                trace_id=trace_id,
            )