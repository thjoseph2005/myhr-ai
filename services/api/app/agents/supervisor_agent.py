from app.agents.context import AgentContext
from app.agents.models import AgentExecutionResult
from app.schemas.chat import ChatMessage

SUPERVISOR_INSTRUCTIONS = """
You are the myhr-ai supervisor agent.

Choose the best available tool for the user's HR question:
- policy_search_tool for handbook, policy, PTO, leave, holiday, benefit, and remote-work questions
- hr_sql_tool for employee, department, manager, headcount, reporting questions, and counts by department
- hybrid_answer_tool for questions that need both policy guidance and structured HR facts in one answer

Rules:
- Use exactly one tool unless the instructions explicitly say otherwise.
- Copy the selected tool's answer and citations into the final response.
- Do not invent citations or fields.
- If the selected tool is not grounded, reply exactly:
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
        if decision.route == "hybrid":
            result = self.context.hybrid_answer_tool.run(question, history)
            return AgentExecutionResult(
                answer=result.answer,
                citations=result.citations,
                grounded=result.grounded,
                tool_name="hybrid_answer_tool",
            )

        result = self.context.policy_search_tool.run(question, history)
        return AgentExecutionResult(
            answer=result.answer,
            citations=result.citations,
            grounded=result.grounded,
            tool_name="policy_search_tool",
        )
