import json

from app.schemas.chat import ChatMessage
from app.schemas.routing import RouteDecision
from app.services.intent_router_service import IntentRouterService
from app.services.openai_service import OpenAIService

ROUTER_SYSTEM_PROMPT = """You are a routing assistant for an HR application.
Choose exactly one route for each user question.

Routes:
- policy_rag: Use for HR policy, PTO, leave, holidays, handbook, benefits, and remote-work policy questions.
- structured_hr: Use for employee, manager, department, title, email, location, reporting line, headcount, counts by department, department summaries, and structured HR database questions.
- hybrid: Use when the question needs both policy knowledge and structured HR data in the same answer.

Respond with valid JSON only:
{"route":"policy_rag|structured_hr|hybrid","reason":"short explanation"}
"""


class LLMRouterService:
    def __init__(self, openai_service: OpenAIService) -> None:
        self.openai_service = openai_service
        self.fallback_router = IntentRouterService()

    def route(self, question: str, history: list[ChatMessage]) -> RouteDecision:
        if not self.openai_service.settings.azure_enabled:
            fallback_route = self.fallback_router.route(question)
            return RouteDecision(route=fallback_route, reason="Fallback heuristic router in mock mode.")

        messages = self._build_messages(question, history)
        try:
            content = self.openai_service.generate_json(messages)
            payload = json.loads(content)
            return RouteDecision.model_validate(payload)
        except Exception:
            fallback_route = self.fallback_router.route(question)
            return RouteDecision(route=fallback_route, reason="Fallback heuristic router after parse failure.")

    @staticmethod
    def _build_messages(question: str, history: list[ChatMessage]) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [{"role": "system", "content": ROUTER_SYSTEM_PROMPT}]
        messages.extend(message.model_dump() for message in history[-4:])
        messages.append({"role": "user", "content": question})
        return messages
