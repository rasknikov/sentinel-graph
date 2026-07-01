import pytest

from packages.ingestion.chunker import (
    DEFAULT_CHUNKING_STRATEGY_VERSION,
    DocumentChunker,
)


def test_chunker_returns_chunks_with_expected_metadata() -> None:
    chunker = DocumentChunker()

    chunks = chunker.chunk(
        document_id="doc_policy_v1",
        tenant_id="tenant_credit",
        version="v1",
        classification="internal",
        content_text="abcdefghij",
        chunk_size=4,
        chunk_overlap=1,
    )

    assert len(chunks) == 4
    assert chunks[0].chunk_id == "doc_policy_v1:v1:0"
    assert chunks[0].tenant_id == "tenant_credit"
    assert chunks[0].version == "v1"
    assert chunks[0].chunk_index == 0
    assert chunks[0].content_text == "abcd"
    assert chunks[0].classification == "internal"
    assert chunks[0].chunking_strategy_version == DEFAULT_CHUNKING_STRATEGY_VERSION
    assert chunks[1].content_text == "defg"
    assert chunks[2].content_text == "ghij"
    assert chunks[3].content_text == "j"


def test_chunker_returns_empty_list_for_blank_content() -> None:
    chunker = DocumentChunker()

    chunks = chunker.chunk(
        document_id="doc_policy_v1",
        tenant_id="tenant_credit",
        version="v1",
        classification="internal",
        content_text="   ",
    )

    assert chunks == []


def test_chunker_rejects_non_positive_chunk_size() -> None:
    chunker = DocumentChunker()

    with pytest.raises(ValueError, match="chunk_size must be greater than zero."):
        chunker.chunk(
            document_id="doc_policy_v1",
            tenant_id="tenant_credit",
            version="v1",
            classification="internal",
            content_text="abcdef",
            chunk_size=0,
        )


def test_chunker_rejects_negative_chunk_overlap() -> None:
    chunker = DocumentChunker()

    with pytest.raises(ValueError, match="chunk_overlap must not be negative."):
        chunker.chunk(
            document_id="doc_policy_v1",
            tenant_id="tenant_credit",
            version="v1",
            classification="internal",
            content_text="abcdef",
            chunk_overlap=-1,
        )


def test_chunker_rejects_overlap_greater_than_or_equal_to_chunk_size() -> None:
    chunker = DocumentChunker()

    with pytest.raises(ValueError, match="chunk_overlap must be smaller than chunk_size."):
        chunker.chunk(
            document_id="doc_policy_v1",
            tenant_id="tenant_credit",
            version="v1",
            classification="internal",
            content_text="abcdef",
            chunk_size=4,
            chunk_overlap=4,
        )
