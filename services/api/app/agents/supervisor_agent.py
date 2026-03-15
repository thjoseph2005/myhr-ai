from app.agents.context import AgentContext
from app.agents.models import AgentExecutionResult
from app.schemas.chat import ChatMessage

SUPERVISOR_INSTRUCTIONS = """
You are the myhr-ai supervisor agent.

Choose the best available tool for the user's HR question:
- policy_search_tool for handbook, policy, PTO, leave, holiday, benefit, and remote-work questions
- hr_sql_tool for employee, department, manager, headcount, and reporting questions

Base answers only on tool output. If the answer is unsupported, reply exactly:
I could not find this in the HR policy document.
""".strip()


class SupervisorAgent:
    def __init__(self, context: AgentContext) -> None:
        self.context = context

    def run(self, question: str, history: list[ChatMessage]) -> AgentExecutionResult:
        decision = self.context.llm_router_service.route(question, history)
        if decision.route == "structured_hr":
            result = self.context.hr_sql_tool.run(question)
            return AgentExecutionResult(
                answer=result.answer,
                citations=result.citations,
                grounded=result.grounded,
                tool_name="hr_sql_tool",
            )

        result = self.context.policy_search_tool.run(question, history)
        return AgentExecutionResult(
            answer=result.answer,
            citations=result.citations,
            grounded=result.grounded,
            tool_name="policy_search_tool",
        )
