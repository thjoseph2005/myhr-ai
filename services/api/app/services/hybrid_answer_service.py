from dataclasses import dataclass

from app.schemas.chat import ChatMessage, ChatRequest, Citation
from app.services.answer_generation_service import AnswerGenerationService
from app.services.grounding_evaluator_service import GroundingEvaluatorService, NOT_FOUND_MESSAGE
from app.tools.hr_sql_tool import HRSQLToolResult
from app.tools.policy_search_tool import PolicyToolResult

HYBRID_SYSTEM_PROMPT = """You are an HR assistant answering a question using two evidence sources:
- policy excerpts and policy answer drafts
- structured HR database answer drafts

Use only the evidence provided. Do not invent facts.
If neither evidence source supports the answer, reply exactly:
I could not find this in the HR policy document.
Keep the answer concise and professional.
"""


@dataclass(slots=True)
class HybridAnswerResult:
    answer: str
    citations: list[Citation]
    grounded: bool


class HybridAnswerService:
    def __init__(
        self,
        answer_generation_service: AnswerGenerationService,
        grounding_evaluator_service: GroundingEvaluatorService,
        max_history_messages: int,
    ) -> None:
        self.answer_generation_service = answer_generation_service
        self.grounding_evaluator_service = grounding_evaluator_service
        self.max_history_messages = max_history_messages

    def build_answer(
        self,
        question: str,
        history: list[ChatMessage],
        policy_result: PolicyToolResult | None,
        sql_result: HRSQLToolResult | None,
    ) -> HybridAnswerResult:
        citations = self._merge_citations(policy_result, sql_result)
        if not citations:
            return HybridAnswerResult(answer=NOT_FOUND_MESSAGE, citations=[], grounded=False)

        openai_service = getattr(self.answer_generation_service, "openai_service", None)
        if not getattr(getattr(openai_service, "settings", None), "azure_enabled", False):
            return HybridAnswerResult(
                answer=self._build_mock_answer(policy_result, sql_result),
                citations=citations,
                grounded=True,
            )

        messages = self._build_messages(question, history, policy_result, sql_result)
        answer = self.answer_generation_service.generate_answer(messages)
        grounded = self.grounding_evaluator_service.is_grounded(answer)
        return HybridAnswerResult(
            answer=answer if grounded else NOT_FOUND_MESSAGE,
            citations=citations if grounded else [],
            grounded=grounded,
        )

    def _build_messages(
        self,
        question: str,
        history: list[ChatMessage],
        policy_result: PolicyToolResult | None,
        sql_result: HRSQLToolResult | None,
    ) -> list[dict[str, str]]:
        history_messages = [message.model_dump() for message in history[-self.max_history_messages :]]
        policy_context = (
            f"Policy answer draft: {policy_result.answer}\n"
            f"Policy citations: {[citation.model_dump() for citation in policy_result.citations]}"
            if policy_result and policy_result.grounded
            else "Policy answer draft: unavailable"
        )
        sql_context = (
            f"Structured HR answer draft: {sql_result.answer}\n"
            f"Structured citations: {[citation.model_dump() for citation in sql_result.citations]}\n"
            f"Structured rows: {sql_result.rows}"
            if sql_result and sql_result.grounded
            else "Structured HR answer draft: unavailable"
        )
        return [
            {"role": "system", "content": HYBRID_SYSTEM_PROMPT},
            *history_messages,
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"{policy_context}\n\n"
                    f"{sql_context}\n\n"
                    "Synthesize a single grounded answer using only the evidence above."
                ),
            },
        ]

    @staticmethod
    def _merge_citations(
        policy_result: PolicyToolResult | None,
        sql_result: HRSQLToolResult | None,
    ) -> list[Citation]:
        citations: list[Citation] = []
        if policy_result and policy_result.grounded:
            citations.extend(policy_result.citations)
        if sql_result and sql_result.grounded:
            citations.extend(sql_result.citations)
        return citations

    @staticmethod
    def _build_mock_answer(
        policy_result: PolicyToolResult | None,
        sql_result: HRSQLToolResult | None,
    ) -> str:
        parts = []
        if policy_result and policy_result.grounded:
            parts.append(policy_result.answer.rstrip("."))
        if sql_result and sql_result.grounded:
            parts.append(sql_result.answer.rstrip("."))
        if not parts:
            return NOT_FOUND_MESSAGE
        return " ".join(parts) + "."
