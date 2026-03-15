from dataclasses import dataclass

from app.core.config import Settings
from app.services.answer_generation_service import AnswerGenerationService
from app.services.grounding_evaluator_service import GroundingEvaluatorService
from app.services.hr_database_service import HRDatabaseService
from app.services.hybrid_answer_service import HybridAnswerService
from app.services.hybrid_question_service import HybridQuestionService
from app.services.llm_router_service import LLMRouterService
from app.services.llm_sql_planner_service import LLMSQLPlannerService
from app.services.prompt_builder_service import PromptBuilderService
from app.services.retriever_service import RetrieverService
from app.services.sql_query_builder_service import SQLQueryBuilderService
from app.services.sql_tool_service import SQLToolService
from app.services.structured_answer_service import StructuredAnswerService
from app.tools.hr_sql_tool import HRSQLTool
from app.tools.hybrid_answer_tool import HybridAnswerTool
from app.tools.policy_search_tool import PolicySearchTool


@dataclass(slots=True)
class AgentContext:
    settings: Settings
    request_id: str
    session_id: str | None
    memory_summary: str | None
    remembered_facts: dict[str, str]
    llm_router_service: LLMRouterService
    retriever_service: RetrieverService
    prompt_builder_service: PromptBuilderService
    answer_generation_service: AnswerGenerationService
    grounding_evaluator_service: GroundingEvaluatorService
    hr_database_service: HRDatabaseService
    hybrid_question_service: HybridQuestionService
    hybrid_answer_service: HybridAnswerService
    sql_query_builder_service: SQLQueryBuilderService
    llm_sql_planner_service: LLMSQLPlannerService
    sql_tool_service: SQLToolService
    structured_answer_service: StructuredAnswerService
    policy_search_tool: PolicySearchTool
    hr_sql_tool: HRSQLTool
    hybrid_answer_tool: HybridAnswerTool
