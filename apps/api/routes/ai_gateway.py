from fastapi import APIRouter, Depends

from packages.ai_gateway.contracts import TextGenerationRequest
from packages.ai_gateway.dependencies import get_ai_gateway_service
from packages.ai_gateway.service import AIGatewayService
from packages.security.dependencies import require_tenant_context
from packages.security.tenant_context import TenantContext


router = APIRouter(tags=["ai-gateway"])


@router.post("/me/generate-text")
async def generate_text_for_current_tenant(
    tenant_context: TenantContext = Depends(require_tenant_context),
    ai_gateway_service: AIGatewayService = Depends(get_ai_gateway_service),
) -> dict[str, str]:
    result = await ai_gateway_service.generate_text(
        TextGenerationRequest(
            tenant_context=tenant_context,
            model_name="gpt-4.1-mini",
            prompt="Return the word SENTINEL.",
            temperature=0.0,
            max_tokens=16,
        )
    )

    return {
        "model_name": result.model_name,
        "output_text": result.output_text,
    }