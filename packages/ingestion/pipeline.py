from packages.ai_gateway.contracts import EmbeddingRequest
from packages.ai_gateway.service import AIGatewayService
from packages.ingestion.chunker import DocumentChunker
from packages.ingestion.contracts import (
    DocumentChunkRecord,
    DocumentRegistrationRequest,
    DocumentVersionRecord,
    EmbeddedChunkRecord,
)
from packages.ingestion.parser import DocumentParser


DEFAULT_EMBEDDING_MODEL_NAME = "text-embedding-3-small"


class DocumentIngestionPipeline:
    def __init__(
        self,
        parser: DocumentParser | None = None,
        chunker: DocumentChunker | None = None,
        ai_gateway_service: AIGatewayService | None = None,
    ) -> None:
        self._parser = parser or DocumentParser()
        self._chunker = chunker or DocumentChunker()
        self._ai_gateway_service = ai_gateway_service or AIGatewayService()

    async def process_document(
        self,
        *,
        request: DocumentRegistrationRequest,
        version_record: DocumentVersionRecord,
    ) -> tuple[list[DocumentChunkRecord], list[EmbeddedChunkRecord]]:
        parsed_content = self._parser.parse(
            source_system=request.source_system,
            content_text=request.content_text,
            trace_id=request.tenant_context.trace_id,
        )

        chunks = self._chunker.chunk(
            document_id=version_record.document_id,
            tenant_id=version_record.tenant_id,
            version=version_record.version,
            classification=version_record.classification,
            content_text=parsed_content,
        )

        embedded_chunks: list[EmbeddedChunkRecord] = []

        for chunk in chunks:
            embedding_result = await self._ai_gateway_service.generate_embedding(
                EmbeddingRequest(
                    tenant_context=request.tenant_context,
                    model_name=DEFAULT_EMBEDDING_MODEL_NAME,
                    input_text=chunk.content_text,
                )
            )
            embedded_chunks.append(
                EmbeddedChunkRecord(
                    chunk_id=chunk.chunk_id,
                    embedding_model_name=embedding_result.model_name,
                    embedding_vector=embedding_result.embedding,
                )
            )

        return chunks, embedded_chunks