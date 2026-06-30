from pydantic import BaseModel, ConfigDict

from packages.security.tenant_context import TenantContext


class TextGenerationRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_context: TenantContext
    model_name: str
    prompt: str
    temperature: float = 0.0
    max_tokens: int = 512


class TextGenerationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    model_name: str
    output_text: str


class EmbeddingRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_context: TenantContext
    model_name: str
    input_text: str


class EmbeddingResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    model_name: str
    embedding: list[float]