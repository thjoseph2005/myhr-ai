from app.core.config import Settings
from app.domain.models import RetrievedChunk
from app.schemas.chat import ChatRequest
from app.services.rag_service import NOT_FOUND_MESSAGE, RAGService


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

    def search(self, query: str, vector: list[float], top_k: int) -> list[RetrievedChunk]:
        assert query
        assert vector
        assert top_k == 3
        return self.chunks


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
    service.openai_service = FakeOpenAIService("Employees receive 15 vacation days per year.")
    service.search_service = FakeSearchService(
        [
            RetrievedChunk(
                chunk_id="hrpolicy-p12-c1",
                document_id="hrpolicy",
                document_name="HRPolicy.pdf",
                page_number=12,
                content="Full-time employees receive 15 vacation days per year.",
                score=1.0,
            )
        ]
    )

    response = await service.answer_question(
        ChatRequest(question="How many vacation days do employees get?", history=[])
    )

    assert response.grounded is True
    assert "15 vacation days" in response.answer
    assert response.citations[0].page_number == 12


async def test_returns_exact_not_found_message_when_answer_is_unsupported() -> None:
    service = RAGService(build_settings())
    service.openai_service = FakeOpenAIService(NOT_FOUND_MESSAGE)
    service.search_service = FakeSearchService(
        [
            RetrievedChunk(
                chunk_id="hrpolicy-p12-c1",
                document_id="hrpolicy",
                document_name="HRPolicy.pdf",
                page_number=12,
                content="Full-time employees receive 15 vacation days per year.",
                score=1.0,
            )
        ]
    )

    response = await service.answer_question(
        ChatRequest(question="Does the policy mention tuition reimbursement?", history=[])
    )

    assert response.grounded is False
    assert response.answer == NOT_FOUND_MESSAGE
    assert response.citations == []
