from openai import AsyncOpenAI

from packages.ai_gateway.contracts import (
    EmbeddingRequest,
    EmbeddingResult,
    TextGenerationRequest,
    TextGenerationResult,
)
from packages.ai_gateway.gateway import AIGateway

class OpenAIGateway(AIGateway):
    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        self.client = client or AsyncOpenAI()

    async def generate_text(
            self,
            request: TextGenerationRequest,
    ) -> TextGenerationResult:
        response = await self.client.responses.create(
            model=request.model_name,
            input=request.prompt,
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
        )

        return TextGenerationResult(
            model_name=request.model_name,
            output_text=response.output_text,
        )
    
    async def generate_embedding(
            self,
            request: EmbeddingRequest,
    ) -> EmbeddingResult:
        response = await self.client.embeddings.create(
            model=request.model_name,
            input=request.input_text,
        )

        return EmbeddingResult(
            model_name=request.model_name,
            embedding=response.data[0].embedding,
        )