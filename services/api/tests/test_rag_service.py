from pathlib import Path

from app.core.config import Settings
from app.domain.models import RetrievedChunk
from app.schemas.chat import ChatRequest
from app.services.grounding_evaluator_service import NOT_FOUND_MESSAGE
from app.services.rag_service import RAGService
from app.schemas.routing import RouteDecision


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
        MOCK_AZURE_MODE=True,
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

    response = await service.answer_question(
        ChatRequest(question="How many employees are there in the company?", history=[])
    )

    assert response.grounded is True
    assert "employees in the HR database" in response.answer
    assert response.citations[0].document_name == "HR Database"
