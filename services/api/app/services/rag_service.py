from functools import lru_cache

from app.core.config import Settings, get_settings
from app.domain.models import RetrievedChunk
from app.schemas.chat import ChatRequest, ChatResponse, Citation
from app.services.answer_generation_service import AnswerGenerationService
from app.services.embedding_service import EmbeddingService
from app.services.grounding_evaluator_service import GroundingEvaluatorService, NOT_FOUND_MESSAGE
from app.services.hr_database_service import HRDatabaseService
from app.services.intent_router_service import IntentRouterService
from app.services.openai_service import OpenAIService
from app.services.prompt_builder_service import PromptBuilderService
from app.services.retriever_service import RetrieverService
from app.services.search_service import SearchService
from app.services.sql_query_builder_service import SQLQueryBuilderService
from app.services.sql_tool_service import SQLToolService
from app.services.structured_answer_service import StructuredAnswerService


class RAGService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.openai_service = OpenAIService(settings)
        self.search_service = SearchService(settings)
        self.embedding_service = EmbeddingService(self.openai_service)
        self.retriever_service = RetrieverService(self.embedding_service, self.search_service)
        self.prompt_builder_service = PromptBuilderService()
        self.answer_generation_service = AnswerGenerationService(self.openai_service)
        self.grounding_evaluator_service = GroundingEvaluatorService()
        self.intent_router_service = IntentRouterService()
        self.hr_database_service = HRDatabaseService(settings)
        self.sql_query_builder_service = SQLQueryBuilderService()
        self.sql_tool_service = SQLToolService(self.hr_database_service)
        self.structured_answer_service = StructuredAnswerService()

    async def answer_question(self, payload: ChatRequest) -> ChatResponse:
        route = self.intent_router_service.route(payload.question)
        if route == "structured_hr":
            return self._answer_structured_question(payload)

        return self._answer_policy_question(payload)

    def _answer_policy_question(self, payload: ChatRequest) -> ChatResponse:
        retrieved = self.retriever_service.retrieve(payload.question, self.settings.default_chat_top_k)

        if not retrieved:
            return ChatResponse(
                answer=NOT_FOUND_MESSAGE,
                citations=[],
                grounded=False,
            )

        messages = self.prompt_builder_service.build_messages(
            payload,
            retrieved,
            self.settings.max_history_messages,
        )
        answer = self.answer_generation_service.generate_answer(messages)
        grounded = self.grounding_evaluator_service.is_grounded(answer)

        return ChatResponse(
            answer=answer if grounded else NOT_FOUND_MESSAGE,
            citations=self._build_citations(retrieved if grounded else []),
            grounded=grounded,
        )

    def _answer_structured_question(self, payload: ChatRequest) -> ChatResponse:
        self.hr_database_service.ensure_database()
        plan = self.sql_query_builder_service.build(payload.question)
        if plan is None:
            return ChatResponse(answer=NOT_FOUND_MESSAGE, citations=[], grounded=False)

        rows = self.sql_tool_service.run_query(plan)
        answer, citations, grounded = self.structured_answer_service.build_answer(plan, rows)
        return ChatResponse(answer=answer, citations=citations, grounded=grounded)

    @staticmethod
    def _build_citations(retrieved: list[RetrievedChunk]) -> list[Citation]:
        return [
            Citation(
                document_id=chunk.document_id,
                document_name=chunk.document_name,
                page_number=chunk.page_number,
                chunk_id=chunk.chunk_id,
                excerpt=chunk.content[:280].strip(),
            )
            for chunk in retrieved
        ]


@lru_cache
def get_rag_service() -> RAGService:
    return RAGService(get_settings())
