import json
import re

from app.schemas.chat import ChatMessage
from app.schemas.hybrid import HybridQuestionPlan
from app.services.openai_service import OpenAIService

HYBRID_PLANNER_PROMPT = """You split HR questions into policy and structured HR sub-questions.

Rules:
- policy_question is for handbook, PTO, leave, holidays, benefits, work-from-home, and policy interpretation.
- structured_question is for employee, department, manager, title, email, location, reporting line, and headcount facts.
- If the user question only needs one side, leave the other field empty.
- Keep each sub-question concise and faithful to the original user request.

Respond with valid JSON only:
{"policy_question":"string","structured_question":"string","reason":"short explanation"}
"""


class HybridQuestionService:
    def __init__(self, openai_service: OpenAIService) -> None:
        self.openai_service = openai_service

    def plan(self, question: str, history: list[ChatMessage]) -> HybridQuestionPlan:
        if self.openai_service.settings.azure_enabled:
            messages: list[dict[str, str]] = [{"role": "system", "content": HYBRID_PLANNER_PROMPT}]
            messages.extend(message.model_dump() for message in history[-4:])
            messages.append({"role": "user", "content": question})
            try:
                payload = json.loads(self.openai_service.generate_json(messages))
                return HybridQuestionPlan.model_validate(payload)
            except Exception:
                pass

        return self._heuristic_plan(question)

    @staticmethod
    def _heuristic_plan(question: str) -> HybridQuestionPlan:
        parts = re.split(r"\s+(?:and|while|plus)\s+", question, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) == 2:
            first, second = parts[0].strip(" ?"), parts[1].strip(" ?")
            if HybridQuestionService._looks_structured(first):
                return HybridQuestionPlan(
                    policy_question=second if not HybridQuestionService._looks_structured(second) else "",
                    structured_question=first,
                    reason="Heuristic split on conjunction.",
                )
            return HybridQuestionPlan(
                policy_question=first,
                structured_question=second if HybridQuestionService._looks_structured(second) else "",
                reason="Heuristic split on conjunction.",
            )

        if HybridQuestionService._looks_structured(question) and HybridQuestionService._looks_policy(question):
            return HybridQuestionPlan(
                policy_question=question,
                structured_question=question,
                reason="Heuristic dual-domain fallback.",
            )

        return HybridQuestionPlan(reason="No hybrid split needed.")

    @staticmethod
    def _looks_policy(question: str) -> bool:
        normalized = question.lower()
        return any(
            keyword in normalized
            for keyword in ["policy", "pto", "vacation", "leave", "holiday", "benefit", "remote", "work from home"]
        )

    @staticmethod
    def _looks_structured(question: str) -> bool:
        normalized = question.lower()
        return any(
            keyword in normalized
            for keyword in [
                "employee",
                "employees",
                "department",
                "manager",
                "count",
                "headcount",
                "title",
                "email",
                "location",
                "who leads",
            ]
        )
