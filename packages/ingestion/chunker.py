import hashlib

from packages.ingestion.contracts import DocumentChunkRecord


DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
DEFAULT_CHUNKING_STRATEGY_VERSION = "chunker_v1"


class DocumentChunker:
    def chunk(
            self,
            *,
            document_id: str,
            tenant_id: str,
            version: str,
            classification: str,
            content_text: str,
            chunk_size: int = DEFAULT_CHUNK_SIZE,
            chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
            chunking_strategy_version: str = DEFAULT_CHUNKING_STRATEGY_VERSION,
    ) -> list[DocumentChunkRecord]:
        normalized_content = content_text.strip()

        if not normalized_content:
            return []
        
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")
        
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must not be negative.")
        
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size.")
        
        chunks: list[DocumentChunkRecord] = []
        start = 0
        chunk_index = 0
        step = chunk_size - chunk_overlap
        
        while start < len(normalized_content):
            end = start + chunk_size
            chunk_text = normalized_content[start:end].strip()

            if chunk_text:
                chunk_id = f"{document_id}:{version}:{chunk_index}"
                content_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()

                chunks.append(
                    DocumentChunkRecord(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        tenant_id=tenant_id,
                        version=version,
                        chunk_index=chunk_index,
                        content_text=chunk_text,
                        content_hash=content_hash,
                        classification=classification,
                        chunking_strategy_version=chunking_strategy_version,
                    )
                )
                chunk_index += 1

            start += step

        return chunks