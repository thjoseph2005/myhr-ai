from dataclasses import dataclass

from app.schemas.chat import Citation
from app.services.grounding_evaluator_service import NOT_FOUND_MESSAGE
from app.services.hr_database_service import HRDatabaseService
from app.services.llm_sql_planner_service import LLMSQLPlannerService
from app.services.sql_query_builder_service import SQLQueryBuilderService, SQLQueryPlan
from app.services.sql_tool_service import SQLToolService
from app.services.structured_answer_service import StructuredAnswerService


@dataclass(slots=True)
class HRSQLToolResult:
    answer: str
    citations: list[Citation]
    grounded: bool
    plan: SQLQueryPlan | None
    rows: list[dict[str, object]]


class HRSQLTool:
    def __init__(
        self,
        hr_database_service: HRDatabaseService,
        sql_query_builder_service: SQLQueryBuilderService,
        llm_sql_planner_service: LLMSQLPlannerService,
        sql_tool_service: SQLToolService,
        structured_answer_service: StructuredAnswerService,
    ) -> None:
        self.hr_database_service = hr_database_service
        self.sql_query_builder_service = sql_query_builder_service
        self.llm_sql_planner_service = llm_sql_planner_service
        self.sql_tool_service = sql_tool_service
        self.structured_answer_service = structured_answer_service

    def run(self, question: str) -> HRSQLToolResult:
        self.hr_database_service.ensure_database()
        plan = self.sql_query_builder_service.build(question)
        if plan is None:
            plan = self.llm_sql_planner_service.build(question)
        if plan is None:
            return HRSQLToolResult(
                answer=NOT_FOUND_MESSAGE,
                citations=[],
                grounded=False,
                plan=None,
                rows=[],
            )

        rows = self.sql_tool_service.run_query(plan)
        answer, citations, grounded = self.structured_answer_service.build_answer(plan, rows)
        return HRSQLToolResult(
            answer=answer,
            citations=citations,
            grounded=grounded,
            plan=plan,
            rows=rows,
        )
