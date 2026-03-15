from app.agents.context import AgentContext
from app.agents.runner import AgentRunnerService
from pathlib import Path

from app.core.config import Settings
from app.domain.models import RetrievedChunk
from app.schemas.chat import ChatRequest
from app.services.grounding_evaluator_service import NOT_FOUND_MESSAGE
from app.services.hybrid_answer_service import HybridAnswerService
from app.services.rag_service import RAGService
from app.services.structured_answer_service import StructuredAnswerService
from app.schemas.routing import RouteDecision
from app.tools.hr_sql_tool import HRSQLTool
from app.tools.hybrid_answer_tool import HybridAnswerTool
from app.tools.policy_search_tool import PolicySearchTool


class FakeOpenAIService:
    def __init__(self, answer: str) -> None:
        self.answer = answer

    def embed_text(self, _: str) -> list[float]:
        return [0.1, 0.2]

    def generate_answer(self, _: list[dict[str, str]]) -> str:
        return self.answer


class FakeSearchService:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self.chunks = chunks

    def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        assert query
        assert top_k == 3
        return self.chunks


class FakeLLMRouterService:
    def __init__(self, route: str) -> None:
        self.route_value = route

    def route(self, question: str, history: list[object]) -> RouteDecision:
        assert question
        assert isinstance(history, list)
        return RouteDecision(route=self.route_value, reason="test")


class FakeLLMSQLPlannerService:
    def __init__(self, plan) -> None:
        self.plan = plan

    def build(self, question: str):
        assert question
        return self.plan


class FakeSDKAgent:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.tools = kwargs["tools"]


class FakeSDKRunner:
    @staticmethod
    async def run(agent, input: str, **kwargs):
        assert kwargs is not None
        normalized = input.lower()
        if "policy" in normalized and "employee" in normalized:
            selected_tool = agent.tools[2]
        elif "employee" in normalized:
            selected_tool = agent.tools[1]
        else:
            selected_tool = agent.tools[0]
        return type("Result", (), {"final_output": selected_tool(input)})()


class FakeSDKSession:
    def __init__(self, session_id: str, database_path: str) -> None:
        self.session_id = session_id
        self.database_path = database_path


def build_settings() -> Settings:
    return Settings(
        APP_ENV="test",
        LOG_LEVEL="INFO",
        API_CORS_ORIGINS=["http://localhost:3000"],
        DEFAULT_CHAT_TOP_K=3,
        DEFAULT_CHAT_TEMPERATURE=0.1,
        MAX_HISTORY_MESSAGES=4,
        INDEXER_BATCH_SIZE=10,
        KNOWLEDGE_BASE_PATH="/tmp/knowledge_base",
        AGENT_MEMORY_PATH="/tmp/test-agent-memory.sqlite3",
        MOCK_AZURE_MODE=True,
    )


def rebind_agent_runner(service: RAGService) -> None:
    service.policy_search_tool = PolicySearchTool(
        service.retriever_service,
        service.prompt_builder_service,
        service.answer_generation_service,
        service.grounding_evaluator_service,
        top_k=service.settings.default_chat_top_k,
        max_history_messages=service.settings.max_history_messages,
    )
    service.structured_answer_service = StructuredAnswerService(
        service.answer_generation_service,
        service.grounding_evaluator_service,
    )
    service.hr_sql_tool = HRSQLTool(
        service.hr_database_service,
        service.sql_query_builder_service,
        service.llm_sql_planner_service,
        service.sql_tool_service,
        service.structured_answer_service,
    )
    service.hybrid_answer_service = HybridAnswerService(
        service.answer_generation_service,
        service.grounding_evaluator_service,
        max_history_messages=service.settings.max_history_messages,
    )
    service.hybrid_answer_tool = HybridAnswerTool(
        service.hybrid_question_service,
        service.hybrid_answer_service,
        service.policy_search_tool,
        service.hr_sql_tool,
    )
    service.agent_runner_service = AgentRunnerService(
        AgentContext(
            settings=service.settings,
            request_id="test",
            session_id=None,
            llm_router_service=service.llm_router_service,
            retriever_service=service.retriever_service,
            prompt_builder_service=service.prompt_builder_service,
            answer_generation_service=service.answer_generation_service,
            grounding_evaluator_service=service.grounding_evaluator_service,
            hr_database_service=service.hr_database_service,
            hybrid_question_service=service.hybrid_question_service,
            hybrid_answer_service=service.hybrid_answer_service,
            sql_query_builder_service=service.sql_query_builder_service,
            llm_sql_planner_service=service.llm_sql_planner_service,
            sql_tool_service=service.sql_tool_service,
            structured_answer_service=service.structured_answer_service,
            policy_search_tool=service.policy_search_tool,
            hr_sql_tool=service.hr_sql_tool,
            hybrid_answer_tool=service.hybrid_answer_tool,
        )
    )


async def test_returns_grounded_answer_with_citations() -> None:
    service = RAGService(build_settings())
    service.llm_router_service = FakeLLMRouterService("policy_rag")
    service.answer_generation_service = FakeOpenAIService("Employees receive 15 vacation days per year.")
    service.retriever_service = FakeSearchService(
        [RetrievedChunk(
            chunk_id="hrpolicy-p12-c1",
            document_id="hrpolicy",
            document_name="HRPolicy.pdf",
            page_number=12,
            content="Full-time employees receive 15 vacation days per year.",
            score=1.0,
        )]
    )
    rebind_agent_runner(service)

    response = await service.answer_question(
        ChatRequest(question="How many vacation days do employees get?", history=[])
    )

    assert response.grounded is True
    assert "15 vacation days" in response.answer
    assert response.citations[0].page_number == 12


async def test_returns_exact_not_found_message_when_answer_is_unsupported() -> None:
    service = RAGService(build_settings())
    service.llm_router_service = FakeLLMRouterService("policy_rag")
    service.answer_generation_service = FakeOpenAIService(NOT_FOUND_MESSAGE)
    service.retriever_service = FakeSearchService(
        [RetrievedChunk(
            chunk_id="hrpolicy-p12-c1",
            document_id="hrpolicy",
            document_name="HRPolicy.pdf",
            page_number=12,
            content="Full-time employees receive 15 vacation days per year.",
            score=1.0,
        )]
    )
    rebind_agent_runner(service)

    response = await service.answer_question(
        ChatRequest(question="Does the policy mention tuition reimbursement?", history=[])
    )

    assert response.grounded is False
    assert response.answer == NOT_FOUND_MESSAGE
    assert response.citations == []


async def test_routes_structured_hr_question_to_sql_path(tmp_path: Path) -> None:
    service = RAGService(
        Settings(
            APP_ENV="test",
            LOG_LEVEL="INFO",
            API_CORS_ORIGINS=["http://localhost:3000"],
            DEFAULT_CHAT_TOP_K=3,
            DEFAULT_CHAT_TEMPERATURE=0.1,
            MAX_HISTORY_MESSAGES=4,
            INDEXER_BATCH_SIZE=10,
            KNOWLEDGE_BASE_PATH="/tmp/knowledge_base",
            HR_DATABASE_PATH=str(tmp_path / "hr.sqlite3"),
            MOCK_AZURE_MODE=True,
        )
    )
    service.llm_router_service = FakeLLMRouterService("structured_hr")
    rebind_agent_runner(service)

    response = await service.answer_question(
        ChatRequest(question="Who is in the Finance department?", history=[])
    )

    assert response.grounded is True
    assert "Finance" in response.answer
    assert response.citations[0].document_name == "HR Database"


async def test_uses_llm_sql_planner_when_rule_planner_has_no_match(tmp_path: Path) -> None:
    service = RAGService(
        Settings(
            APP_ENV="test",
            LOG_LEVEL="INFO",
            API_CORS_ORIGINS=["http://localhost:3000"],
            DEFAULT_CHAT_TOP_K=3,
            DEFAULT_CHAT_TEMPERATURE=0.1,
            MAX_HISTORY_MESSAGES=4,
            INDEXER_BATCH_SIZE=10,
            KNOWLEDGE_BASE_PATH="/tmp/knowledge_base",
            HR_DATABASE_PATH=str(tmp_path / "hr.sqlite3"),
            MOCK_AZURE_MODE=True,
        )
    )
    service.llm_router_service = FakeLLMRouterService("structured_hr")
    service.llm_sql_planner_service = FakeLLMSQLPlannerService(
        type(
            "Plan",
            (),
            {
                "intent": "company_headcount",
                "sql": "SELECT COUNT(*) AS employee_count FROM employees",
                "parameters": [],
                "description": "Company headcount",
            },
        )()
    )
    rebind_agent_runner(service)

    response = await service.answer_question(
        ChatRequest(question="How many employees are there in the company?", history=[])
    )

    assert response.grounded is True
    assert "employees in the HR database" in response.answer
    assert response.citations[0].document_name == "HR Database"


async def test_uses_session_memory_when_session_id_is_provided(tmp_path: Path) -> None:
    service = RAGService(
        Settings(
            APP_ENV="test",
            LOG_LEVEL="INFO",
            API_CORS_ORIGINS=["http://localhost:3000"],
            DEFAULT_CHAT_TOP_K=3,
            DEFAULT_CHAT_TEMPERATURE=0.1,
            MAX_HISTORY_MESSAGES=4,
            INDEXER_BATCH_SIZE=10,
            KNOWLEDGE_BASE_PATH="/tmp/knowledge_base",
            AGENT_MEMORY_PATH=str(tmp_path / "agent-memory.sqlite3"),
            MOCK_AZURE_MODE=True,
        )
    )
    service.llm_router_service = FakeLLMRouterService("policy_rag")
    service.answer_generation_service = FakeOpenAIService("Employees receive 15 vacation days per year.")
    service.retriever_service = FakeSearchService(
        [RetrievedChunk(
            chunk_id="hrpolicy-p12-c1",
            document_id="hrpolicy",
            document_name="HRPolicy.pdf",
            page_number=12,
            content="Full-time employees receive 15 vacation days per year.",
            score=1.0,
        )]
    )
    rebind_agent_runner(service)

    first = await service.answer_question(
        ChatRequest(
            question="How many vacation days do employees get?",
            history=[],
            session_id="demo-session",
        )
    )
    second = await service.answer_question(
        ChatRequest(
            question="Can you remind me again?",
            history=[],
            session_id="demo-session",
        )
    )

    assert first.grounded is True
    assert second.grounded is True
    stored_history = service.agent_runner_service.session_store.load_history("demo-session")
    assert len(stored_history) == 4


async def test_prefers_sdk_supervisor_path_when_enabled(tmp_path: Path) -> None:
    original_agent_class = AgentRunnerService.sdk_agent_class
    original_runner = AgentRunnerService.sdk_runner
    original_function_tool = AgentRunnerService.sdk_function_tool
    original_session_class = AgentRunnerService.sdk_session_class
    original_set_client = AgentRunnerService.sdk_set_client
    original_set_api = AgentRunnerService.sdk_set_api
    original_disable_tracing = AgentRunnerService.sdk_disable_tracing
    original_async_client_class = AgentRunnerService.sdk_async_client_class

    AgentRunnerService.sdk_agent_class = FakeSDKAgent
    AgentRunnerService.sdk_runner = FakeSDKRunner
    AgentRunnerService.sdk_function_tool = staticmethod(lambda func: func)
    AgentRunnerService.sdk_session_class = FakeSDKSession
    AgentRunnerService.sdk_set_client = staticmethod(lambda *args, **kwargs: None)
    AgentRunnerService.sdk_set_api = staticmethod(lambda *args, **kwargs: None)
    AgentRunnerService.sdk_disable_tracing = staticmethod(lambda *args, **kwargs: None)
    AgentRunnerService.sdk_async_client_class = type(
        "FakeAsyncClient",
        (),
        {"__init__": lambda self, **kwargs: None},
    )

    try:
        service = RAGService(
            Settings(
                APP_ENV="test",
                LOG_LEVEL="INFO",
                API_CORS_ORIGINS=["http://localhost:3000"],
                DEFAULT_CHAT_TOP_K=3,
                DEFAULT_CHAT_TEMPERATURE=0.1,
                MAX_HISTORY_MESSAGES=4,
                INDEXER_BATCH_SIZE=10,
                KNOWLEDGE_BASE_PATH="/tmp/knowledge_base",
                HR_DATABASE_PATH=str(tmp_path / "hr.sqlite3"),
                AGENT_MEMORY_PATH=str(tmp_path / "agent-memory.sqlite3"),
                OPENAI_AGENTS_ENABLED=True,
                MOCK_AZURE_MODE=False,
                AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com",
                AZURE_OPENAI_API_KEY="key",
                AZURE_OPENAI_CHAT_DEPLOYMENT="chat-deployment",
                AZURE_OPENAI_EMBEDDING_DEPLOYMENT="embedding-deployment",
                AZURE_SEARCH_ENDPOINT="https://example.search.windows.net",
                AZURE_SEARCH_API_KEY="search-key",
                AZURE_SEARCH_INDEX_NAME="hr-policy-index",
            )
        )
        service.llm_router_service = FakeLLMRouterService("policy_rag")
        rebind_agent_runner(service)

        response = await service.answer_question(
            ChatRequest(
                question="How many employees are there in the company?",
                history=[],
                session_id="sdk-session",
            )
        )

        assert response.grounded is True
        assert "employees in the HR database" in response.answer
        assert response.citations[0].document_name == "HR Database"
    finally:
        AgentRunnerService.sdk_agent_class = original_agent_class
        AgentRunnerService.sdk_runner = original_runner
        AgentRunnerService.sdk_function_tool = original_function_tool
        AgentRunnerService.sdk_session_class = original_session_class
        AgentRunnerService.sdk_set_client = original_set_client
        AgentRunnerService.sdk_set_api = original_set_api
        AgentRunnerService.sdk_disable_tracing = original_disable_tracing
        AgentRunnerService.sdk_async_client_class = original_async_client_class


async def test_answers_hybrid_question_with_combined_citations(tmp_path: Path) -> None:
    service = RAGService(
        Settings(
            APP_ENV="test",
            LOG_LEVEL="INFO",
            API_CORS_ORIGINS=["http://localhost:3000"],
            DEFAULT_CHAT_TOP_K=3,
            DEFAULT_CHAT_TEMPERATURE=0.1,
            MAX_HISTORY_MESSAGES=4,
            INDEXER_BATCH_SIZE=10,
            KNOWLEDGE_BASE_PATH="/tmp/knowledge_base",
            HR_DATABASE_PATH=str(tmp_path / "hr.sqlite3"),
            AGENT_MEMORY_PATH=str(tmp_path / "agent-memory.sqlite3"),
            MOCK_AZURE_MODE=True,
        )
    )
    service.llm_router_service = FakeLLMRouterService("hybrid")
    service.answer_generation_service = FakeOpenAIService(
        "Parental leave is available under the handbook policy. There are 12 employees in the HR database."
    )
    service.retriever_service = FakeSearchService(
        [RetrievedChunk(
            chunk_id="hrpolicy-p20-c1",
            document_id="hrpolicy",
            document_name="HRPolicy.pdf",
            page_number=20,
            content="Eligible employees may take parental leave under the handbook policy.",
            score=1.0,
        )]
    )
    rebind_agent_runner(service)

    response = await service.answer_question(
        ChatRequest(
            question="What is the parental leave policy and how many employees are there in this company?",
            history=[],
        )
    )

    assert response.grounded is True
    assert "Parental leave" in response.answer
    assert any(citation.document_name == "HRPolicy.pdf" for citation in response.citations)
    assert any(citation.document_name == "HR Database" for citation in response.citations)
