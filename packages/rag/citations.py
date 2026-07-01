from pydantic import BaseModel, ConfigDict

from packages.rag.contracts import RetrievedChunk


class Citation(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_id: str
    document_version: str
    chunk_id: str
    source: str
    confidence: float


def build_citations(
    chunks: tuple[RetrievedChunk, ...],
) -> tuple[Citation, ...]:
    return tuple(
        Citation(
            document_id=chunk.document_id,
            document_version=chunk.version,
            chunk_id=chunk.chunk_id,
            source=chunk.document_id,
            confidence=chunk.score,
        )
        for chunk in chunks
    )