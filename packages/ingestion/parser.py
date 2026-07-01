from packages.common.errors import DomainError, ErrorCode


SUPPORTED_SOURCE_SYSTEMS = {
    "sharepoint",
    "confluence",
    "notion",
    "markdown",
    "plain_text",
}


class DocumentParser:
    def parse(
            self,
            *,
            source_system: str,
            content_text: str,
            trace_id: str,
    ) -> str:
        normalized_source_system = source_system.strip().lower()
        normalized_content = content_text.strip()

        if not normalized_source_system:
            raise DomainError(
                code=ErrorCode.OUTPUT_VALIDATION_FAILED,
                message="Source system is required.",
                trace_id=trace_id,
            )
        
        if normalized_source_system not in SUPPORTED_SOURCE_SYSTEMS:
            raise DomainError(
                code=ErrorCode.OUTPUT_VALIDATION_FAILED,
                message="Source system is not supported.",
                trace_id=trace_id,
            )
        
        if not normalized_content:
            raise DomainError(
                code=ErrorCode.OUTPUT_VALIDATION_FAILED,
                message="Document content is required.",
                trace_id=trace_id,
            )
        
        return normalized_content
