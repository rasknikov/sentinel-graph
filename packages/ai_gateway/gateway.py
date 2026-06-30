from typing import Protocol

from packages.ai_gateway.contracts import(
    EmbeddingRequest,
    EmbeddingResult,
    TextGenerationRequest,
    TextGenerationResult,
)


class AIGateway(Protocol):
    async def generate_text(
            self,
            request: TextGenerationRequest,
    ) -> TextGenerationResult:
        ...

    async def generate_embedding(
            self,
            request: EmbeddingRequest,
    ) -> EmbeddingResult:
        ...