from functools import lru_cache

from app.agents.context import AgentContext
from app.agents.runner import AgentRunnerService
from app.core.config import Settings, get_settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.answer_generation_service import AnswerGenerationService
from app.services.embedding_service import EmbeddingService
from app.services.grounding_evaluator_service import GroundingEvaluatorService
from app.services.hr_database_service import HRDatabaseService
from app.services.hybrid_answer_service import HybridAnswerService
from app.services.hybrid_question_service import HybridQuestionService
from app.services.llm_sql_repair_service import LLMSQLRepairService
from app.services.llm_router_service import LLMRouterService
from app.services.llm_sql_planner_service import LLMSQLPlannerService
from app.services.openai_service import OpenAIService
from app.services.prompt_builder_service import PromptBuilderService
from app.services.retriever_service import RetrieverService
from app.services.search_service import SearchService
from app.services.sql_query_builder_service import SQLQueryBuilderService
from app.services.sql_tool_service import SQLToolService
from app.services.structured_answer_service import StructuredAnswerService
from app.tools.hr_sql_tool import HRSQLTool
from app.tools.hybrid_answer_tool import HybridAnswerTool
from app.tools.policy_search_tool import PolicySearchTool


class RAGService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.openai_service = OpenAIService(settings)
        self.search_service = SearchService(settings)
        self.embedding_service = EmbeddingService(self.openai_service)
        self.retriever_service = RetrieverService(self.embedding_service, self.search_service)
        self.prompt_builder_service = PromptBuilderService()
        self.answer_generation_service = AnswerGenerationService(self.openai_service)
        self.grounding_evaluator_service = GroundingEvaluatorService()
        self.llm_router_service = LLMRouterService(self.openai_service)
        self.hr_database_service = HRDatabaseService(settings)
        self.hybrid_question_service = HybridQuestionService(self.openai_service)
        self.hybrid_answer_service = HybridAnswerService(
            self.answer_generation_service,
            self.grounding_evaluator_service,
            max_history_messages=self.settings.max_history_messages,
        )
        self.sql_query_builder_service = SQLQueryBuilderService()
        self.llm_sql_planner_service = LLMSQLPlannerService(
            self.openai_service,
            self.hr_database_service,
        )
        self.llm_sql_repair_service = LLMSQLRepairService(self.openai_service)
        self.sql_tool_service = SQLToolService(self.hr_database_service)
        self.structured_answer_service = StructuredAnswerService(
            self.answer_generation_service,
            self.grounding_evaluator_service,
        )
        self.policy_search_tool = PolicySearchTool(
            self.retriever_service,
            self.prompt_builder_service,
            self.answer_generation_service,
            self.grounding_evaluator_service,
            top_k=self.settings.default_chat_top_k,
            max_history_messages=self.settings.max_history_messages,
        )
        self.hr_sql_tool = HRSQLTool(
            self.hr_database_service,
            self.sql_query_builder_service,
            self.llm_sql_planner_service,
            self.llm_sql_repair_service,
            self.sql_tool_service,
            self.structured_answer_service,
        )
        self.hybrid_answer_tool = HybridAnswerTool(
            self.hybrid_question_service,
            self.hybrid_answer_service,
            self.policy_search_tool,
            self.hr_sql_tool,
        )
        self.agent_runner_service = AgentRunnerService(
            AgentContext(
                settings=self.settings,
                request_id="bootstrap",
                session_id=None,
                memory_summary=None,
                remembered_facts={},
                llm_router_service=self.llm_router_service,
                retriever_service=self.retriever_service,
                prompt_builder_service=self.prompt_builder_service,
                answer_generation_service=self.answer_generation_service,
                grounding_evaluator_service=self.grounding_evaluator_service,
                hr_database_service=self.hr_database_service,
                hybrid_question_service=self.hybrid_question_service,
                hybrid_answer_service=self.hybrid_answer_service,
                sql_query_builder_service=self.sql_query_builder_service,
                llm_sql_planner_service=self.llm_sql_planner_service,
                sql_tool_service=self.sql_tool_service,
                structured_answer_service=self.structured_answer_service,
                policy_search_tool=self.policy_search_tool,
                hr_sql_tool=self.hr_sql_tool,
                hybrid_answer_tool=self.hybrid_answer_tool,
            )
        )

    async def answer_question(self, payload: ChatRequest) -> ChatResponse:
        return await self.agent_runner_service.run_chat(payload)


@lru_cache
def get_rag_service() -> RAGService:
    return RAGService(get_settings())
