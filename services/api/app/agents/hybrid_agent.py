from app.agents.context import AgentContext
from app.agents.models import AgentExecutionResult
from app.schemas.chat import ChatMessage


class HybridAgent:
    def __init__(self, context: AgentContext) -> None:
        self.context = context

    def run(self, question: str, history: list[ChatMessage]) -> AgentExecutionResult:
        result = self.context.hybrid_answer_tool.run(question, history)
        return AgentExecutionResult(
            answer=result.answer,
            citations=result.citations,
            grounded=result.grounded,
            tool_name="hybrid_answer_tool",
        )
