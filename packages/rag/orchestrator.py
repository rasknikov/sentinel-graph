from pydantic import BaseModel, ConfigDict

from packages.ai_gateway.contracts import TextGenerationRequest
from packages.ai_gateway.service import AIGatewayService
from packages.rag.citations import Citation, build_citations
from packages.rag.context_builder import build_context
from packages.rag.contracts import RetrievalFilters, RetrievalRequest
from packages.rag.grounding import validate_grounding
from packages.rag.vector_access_gateway import VectorAccessGateway
from packages.security.tenant_context import TenantContext


class GroundedAnswerResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    answer: str
    citations: tuple[Citation, ...]
    trace_id: str
    requires_human_review: bool = False


class RAGOrchestrator:
    def __init__(
        self,
        vector_access_gateway: VectorAccessGateway,
        ai_gateway_service: AIGatewayService,
    ) -> None:
        self._vector_access_gateway = vector_access_gateway
        self._ai_gateway_service = ai_gateway_service

    async def answer(
        self,
        *,
        tenant_context: TenantContext,
        query_text: str,
        top_k: int = 5,
        filters: RetrievalFilters | None = None,
    ) -> GroundedAnswerResult:
        retrieval_result = await self._vector_access_gateway.search(
            RetrievalRequest(
                tenant_context=tenant_context,
                query_text=query_text,
                top_k=top_k,
                filters=filters or RetrievalFilters(),
            )
        )

        context_text = build_context(retrieval_result.chunks)
        citations = build_citations(retrieval_result.chunks)

        answer_result = await self._ai_gateway_service.generate_text(
            TextGenerationRequest(
                tenant_context=tenant_context,
                model_name="gpt-4.1-mini",
                prompt=self._build_prompt(
                    query_text=query_text,
                    context_text=context_text,
                ),
                temperature=0.0,
                max_tokens=512,
            )
        )

        validate_grounding(
            answer_text=answer_result.output_text,
            citations=citations,
            trace_id=tenant_context.trace_id,
        )

        return GroundedAnswerResult(
            answer=answer_result.output_text,
            citations=citations,
            trace_id=tenant_context.trace_id,
            requires_human_review=False,
        )

    def _build_prompt(
        self,
        *,
        query_text: str,
        context_text: str,
    ) -> str:
        return "\n\n".join(
            [
                "Answer the user strictly from the provided sources.",
                "If the sources are insufficient, do not invent facts.",
                f"User question: {query_text}",
                f"Sources:\n{context_text}",
            ]
        )