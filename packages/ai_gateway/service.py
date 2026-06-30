from packages.ai_gateway.contracts import (
    EmbeddingRequest,
    EmbeddingResult,
    TextGenerationRequest,
    TextGenerationResult,
)
from packages.ai_gateway.gateway import AIGateway
from packages.ai_gateway.openai_gateway import OpenAIGateway
from packages.common.errors import DomainError, ErrorCode


ALLOWED_MODEL_NAMES = {
    "gpt-4.1-mini",
    "text-embedding-3-small",
}


class AIGatewayService:
    def __init__(self, gateway: AIGateway | None = None) -> None:
        self.gateway = gateway or OpenAIGateway()

    async def generate_text(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResult:
        self._validate_model_name(request.model_name, request.tenant_context.trace_id)
        try:
            return await self.gateway.generate_text(request)
        except DomainError:
            raise
        except Exception as exc:
            raise DomainError(
                code=ErrorCode.MODEL_UNAVAILABLE,
                message="Model provider is unavailable.",
                trace_id=request.tenant_context.trace_id,
                cause=exc,
            ) from exc

    async def generate_embedding(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResult:
        self._validate_model_name(request.model_name, request.tenant_context.trace_id)
        try:
            return await self.gateway.generate_embedding(request)
        except DomainError:
            raise
        except Exception as exc:
            raise DomainError(
                code=ErrorCode.MODEL_UNAVAILABLE,
                message="Model provider is unavailable.",
                trace_id=request.tenant_context.trace_id,
                cause=exc,
            ) from exc

    def _validate_model_name(self, model_name: str, trace_id: str) -> None:
        normalized_model_name = model_name.strip()

        if not normalized_model_name:
            raise DomainError(
                code=ErrorCode.MODEL_NOT_ALLOWED,
                message="Model name is required.",
                trace_id=trace_id,
            )

        if normalized_model_name not in ALLOWED_MODEL_NAMES:
            raise DomainError(
                code=ErrorCode.MODEL_NOT_ALLOWED,
                message="Model is not allowed.",
                trace_id=trace_id,
            )
