from dataclasses import dataclass

from app.schemas.chat import ChatMessage, Citation
from app.services.hybrid_answer_service import HybridAnswerResult, HybridAnswerService
from app.services.hybrid_question_service import HybridQuestionService
from app.tools.hr_sql_tool import HRSQLTool, HRSQLToolResult
from app.tools.policy_search_tool import PolicySearchTool, PolicyToolResult


@dataclass(slots=True)
class HybridToolResult:
    answer: str
    citations: list[Citation]
    grounded: bool
    policy_result: PolicyToolResult | None
    sql_result: HRSQLToolResult | None


class HybridAnswerTool:
    def __init__(
        self,
        hybrid_question_service: HybridQuestionService,
        hybrid_answer_service: HybridAnswerService,
        policy_search_tool: PolicySearchTool,
        hr_sql_tool: HRSQLTool,
    ) -> None:
        self.hybrid_question_service = hybrid_question_service
        self.hybrid_answer_service = hybrid_answer_service
        self.policy_search_tool = policy_search_tool
        self.hr_sql_tool = hr_sql_tool

    def run(self, question: str, history: list[ChatMessage]) -> HybridToolResult:
        plan = self.hybrid_question_service.plan(question, history)
        policy_question = plan.policy_question or question
        structured_question = plan.structured_question or question

        policy_result = self.policy_search_tool.run(policy_question, history)
        sql_result = self.hr_sql_tool.run(structured_question)
        final_result: HybridAnswerResult = self.hybrid_answer_service.build_answer(
            question,
            history,
            policy_result,
            sql_result,
        )
        return HybridToolResult(
            answer=final_result.answer,
            citations=final_result.citations,
            grounded=final_result.grounded,
            policy_result=policy_result,
            sql_result=sql_result,
        )
