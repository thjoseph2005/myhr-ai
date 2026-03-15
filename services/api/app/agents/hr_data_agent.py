from app.agents.context import AgentContext
from app.agents.models import AgentExecutionResult


class HRDataAgent:
    def __init__(self, context: AgentContext) -> None:
        self.context = context

    def run(self, question: str) -> AgentExecutionResult:
        result = self.context.hr_sql_tool.run(question)
        return AgentExecutionResult(
            answer=result.answer,
            citations=result.citations,
            grounded=result.grounded,
            tool_name="hr_sql_tool",
        )
