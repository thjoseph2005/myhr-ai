from fastapi.testclient import TestClient

from app.main import app
from app.schemas.chat import ChatResponse, Citation
from app.schemas.documents import DocumentInfo, DocumentStatusResponse, ReindexResponse
from app.services.document_service import get_document_service
from app.services.rag_service import get_rag_service


class FakeRAGService:
    async def answer_question(self, _: object) -> ChatResponse:
        return ChatResponse(
            answer="Employees receive 15 vacation days per year.",
            grounded=True,
            citations=[
                Citation(
                    document_name="HRPolicy.pdf",
                    page_number=12,
                    chunk_id="hrpolicy-p12-c1",
                    excerpt="Full-time employees receive 15 vacation days per year.",
                    document_id="hrpolicy",
                )
            ],
        )


class FakeDocumentService:
    def get_status(self) -> DocumentStatusResponse:
        return DocumentStatusResponse(
            knowledge_base_path="/tmp/knowledge_base",
            discovered_documents=[
                DocumentInfo(
                    document_id="hrpolicy",
                    document_name="HRPolicy.pdf",
                    path="/tmp/knowledge_base/HRPolicy.pdf",
                    indexed=True,
                    indexed_chunks=4,
                )
            ],
            indexing_status="completed",
            last_indexed_at="2026-03-14T12:00:00+00:00",
            indexed_document_count=1,
            total_indexed_chunks=4,
            azure_enabled=False,
        )

    def reindex(self) -> ReindexResponse:
        return ReindexResponse(
            indexed_documents=1,
            indexed_chunks=4,
            indexing_status="completed",
            last_indexed_at="2026-03-14T12:00:00+00:00",
        )


def test_chat_endpoint_returns_expected_contract() -> None:
    app.dependency_overrides[get_rag_service] = FakeRAGService
    client = TestClient(app)

    response = client.post("/api/chat", json={"question": "What is PTO?", "history": []})

    assert response.status_code == 200
    payload = response.json()
    assert payload["grounded"] is True
    assert payload["citations"][0]["document_name"] == "HRPolicy.pdf"
    app.dependency_overrides.clear()


def test_documents_status_endpoint_returns_status_payload() -> None:
    app.dependency_overrides[get_document_service] = FakeDocumentService
    client = TestClient(app)

    response = client.get("/api/documents/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["knowledge_base_path"] == "/tmp/knowledge_base"
    assert payload["discovered_documents"][0]["document_name"] == "HRPolicy.pdf"
    assert payload["discovered_documents"][0]["indexed"] is True
    assert payload["total_indexed_chunks"] == 4
    app.dependency_overrides.clear()
