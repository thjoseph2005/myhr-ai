from app.schemas.chat import ChatMessage
from app.services.llm_router_service import LLMRouterService


class RaisingOpenAIService:
    def __init__(self, azure_enabled: bool = True) -> None:
        self.settings = type("SettingsStub", (), {"azure_enabled": azure_enabled})()

    def generate_json(self, _: list[dict[str, str]]) -> str:
        raise RuntimeError("router unavailable")


def test_falls_back_to_heuristic_router_when_llm_router_raises() -> None:
    service = LLMRouterService(RaisingOpenAIService())

    decision = service.route("How many depart ments are there?", [ChatMessage(role="user", content="hi")])

    assert decision.route == "structured_hr"
    assert "Fallback heuristic router" in decision.reason


def test_falls_back_to_hybrid_route_when_question_needs_policy_and_structure() -> None:
    service = LLMRouterService(RaisingOpenAIService())

    decision = service.route(
        "What is the parental leave policy and how many employees are there in this company?",
        [ChatMessage(role="user", content="hi")],
    )

    assert decision.route == "hybrid"
