from packages.rag.contracts import RetrievedChunk


def build_context(
    chunks: tuple[RetrievedChunk, ...],
) -> str:
    if not chunks:
        return ""

    parts: list[str] = []

    for index, chunk in enumerate(chunks, start=1):
        parts.append(
            "\n".join(
                [
                    f"[Source {index}]",
                    f"document_id: {chunk.document_id}",
                    f"document_version: {chunk.version}",
                    f"chunk_id: {chunk.chunk_id}",
                    f"classification: {chunk.classification}",
                    f"content: {chunk.content_text}",
                ]
            )
        )

    return "\n\n".join(parts)