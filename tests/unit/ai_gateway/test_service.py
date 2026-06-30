import pytest

from packages.ai_gateway.contracts import (
    EmbeddingRequest,
    EmbeddingResult,
    TextGenerationRequest,
    TextGenerationResult,
)
from packages.ai_gateway.service import AIGatewayService
from packages.common.errors import DomainError, ErrorCode
from packages.security.tenant_context import TenantContext


def build_tenant_context() -> TenantContext:
    return TenantContext(
        tenant_id="tenant_credit",
        user_id="user_123",
        roles=("analyst",),
        scopes=("rag:query",),
        department="credit",
        clearance_level="internal",
        session_id="session_abc",
        request_id="req_123",
        trace_id="trace_123",
        environment="test",
        auth_provider="https://identity.example.com",
    )


class RecordingGateway:
    def __init__(self) -> None:
        self.last_text_request: TextGenerationRequest | None = None
        self.last_embedding_request: EmbeddingRequest | None = None

    async def generate_text(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResult:
        self.last_text_request = request
        return TextGenerationResult(
            model_name=request.model_name,
            output_text="SENTINEL",
        )

    async def generate_embedding(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResult:
        self.last_embedding_request = request
        return EmbeddingResult(
            model_name=request.model_name,
            embedding=[0.1, 0.2, 0.3],
        )


class FailingGateway:
    async def generate_text(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResult:
        raise RuntimeError("provider down")

    async def generate_embedding(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResult:
        raise RuntimeError("provider down")


@pytest.mark.asyncio
async def test_generate_text_rejects_blank_model_name() -> None:
    service = AIGatewayService(gateway=RecordingGateway())

    with pytest.raises(DomainError) as exc_info:
        await service.generate_text(
            TextGenerationRequest(
                tenant_context=build_tenant_context(),
                model_name="   ",
                prompt="Return the word SENTINEL.",
            )
        )

    assert exc_info.value.code is ErrorCode.MODEL_NOT_ALLOWED
    assert exc_info.value.trace_id == "trace_123"


@pytest.mark.asyncio
async def test_generate_text_rejects_disallowed_model_name() -> None:
    service = AIGatewayService(gateway=RecordingGateway())

    with pytest.raises(DomainError) as exc_info:
        await service.generate_text(
            TextGenerationRequest(
                tenant_context=build_tenant_context(),
                model_name="gpt-unknown",
                prompt="Return the word SENTINEL.",
            )
        )

    assert exc_info.value.code is ErrorCode.MODEL_NOT_ALLOWED
    assert exc_info.value.message == "Model is not allowed."


@pytest.mark.asyncio
async def test_generate_text_delegates_to_gateway_for_allowed_model() -> None:
    gateway = RecordingGateway()
    service = AIGatewayService(gateway=gateway)

    result = await service.generate_text(
        TextGenerationRequest(
            tenant_context=build_tenant_context(),
            model_name="gpt-4.1-mini",
            prompt="Return the word SENTINEL.",
        )
    )

    assert gateway.last_text_request is not None
    assert gateway.last_text_request.model_name == "gpt-4.1-mini"
    assert result.output_text == "SENTINEL"


@pytest.mark.asyncio
async def test_generate_embedding_delegates_to_gateway_for_allowed_model() -> None:
    gateway = RecordingGateway()
    service = AIGatewayService(gateway=gateway)

    result = await service.generate_embedding(
        EmbeddingRequest(
            tenant_context=build_tenant_context(),
            model_name="text-embedding-3-small",
            input_text="credit policy",
        )
    )

    assert gateway.last_embedding_request is not None
    assert gateway.last_embedding_request.model_name == "text-embedding-3-small"
    assert result.embedding == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_generate_text_wraps_provider_error_as_domain_error() -> None:
    service = AIGatewayService(gateway=FailingGateway())

    with pytest.raises(DomainError) as exc_info:
        await service.generate_text(
            TextGenerationRequest(
                tenant_context=build_tenant_context(),
                model_name="gpt-4.1-mini",
                prompt="Return the word SENTINEL.",
            )
        )

    assert exc_info.value.code is ErrorCode.MODEL_UNAVAILABLE
    assert exc_info.value.message == "Model provider is unavailable."
    assert exc_info.value.trace_id == "trace_123"
