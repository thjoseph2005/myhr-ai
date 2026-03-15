from dataclasses import dataclass

from app.domain.models import RetrievedChunk
from app.schemas.chat import ChatMessage, ChatRequest, Citation
from app.services.answer_generation_service import AnswerGenerationService
from app.services.grounding_evaluator_service import GroundingEvaluatorService, NOT_FOUND_MESSAGE
from app.services.prompt_builder_service import PromptBuilderService
from app.services.retriever_service import RetrieverService


@dataclass(slots=True)
class PolicyToolResult:
    answer: str
    citations: list[Citation]
    grounded: bool
    retrieved_chunks: list[RetrievedChunk]


class PolicySearchTool:
    def __init__(
        self,
        retriever_service: RetrieverService,
        prompt_builder_service: PromptBuilderService,
        answer_generation_service: AnswerGenerationService,
        grounding_evaluator_service: GroundingEvaluatorService,
        top_k: int,
        max_history_messages: int,
    ) -> None:
        self.retriever_service = retriever_service
        self.prompt_builder_service = prompt_builder_service
        self.answer_generation_service = answer_generation_service
        self.grounding_evaluator_service = grounding_evaluator_service
        self.top_k = top_k
        self.max_history_messages = max_history_messages

    def run(self, question: str, history: list[ChatMessage]) -> PolicyToolResult:
        retrieved = self.retriever_service.retrieve(question, self.top_k)
        if not retrieved:
            return PolicyToolResult(
                answer=NOT_FOUND_MESSAGE,
                citations=[],
                grounded=False,
                retrieved_chunks=[],
            )

        messages = self.prompt_builder_service.build_messages(
            ChatRequest(question=question, history=history),
            retrieved,
            self.max_history_messages,
        )
        answer = self.answer_generation_service.generate_answer(messages)
        grounded = self.grounding_evaluator_service.is_grounded(answer)
        citations = self._build_citations(retrieved if grounded else [])
        return PolicyToolResult(
            answer=answer if grounded else NOT_FOUND_MESSAGE,
            citations=citations,
            grounded=grounded,
            retrieved_chunks=retrieved,
        )

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
