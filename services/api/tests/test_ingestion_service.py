from pathlib import Path

from app.core.config import Settings
from app.domain.models import ExtractedPage
from app.services.chunking_service import ChunkingService
from app.services.ingestion_service import IngestionService


def build_settings(tmp_path: Path) -> Settings:
    return Settings(
        APP_ENV="test",
        LOG_LEVEL="INFO",
        API_CORS_ORIGINS=["http://localhost:3000"],
        KNOWLEDGE_BASE_PATH=str(tmp_path),
        MOCK_AZURE_MODE=True,
    )


def test_extract_chunks_preserves_page_mapping(monkeypatch, tmp_path: Path) -> None:
    def fake_extract_pages(_: Path) -> list[ExtractedPage]:
        return [
            ExtractedPage(
                document_id="hrpolicy",
                document_name="HRPolicy.pdf",
                page_number=1,
                text="Vacation policy content on page one.",
            ),
            ExtractedPage(
                document_id="hrpolicy",
                document_name="HRPolicy.pdf",
                page_number=2,
                text="Remote work policy content on page two.",
            ),
        ]

    service = IngestionService(build_settings(tmp_path))
    monkeypatch.setattr(service.pdf_extraction_service, "extract_pages", fake_extract_pages)

    chunks = service.extract_chunks(tmp_path / "HRPolicy.pdf")

    assert len(chunks) == 2
    assert chunks[0].page_number == 1
    assert chunks[1].page_number == 2
    assert chunks[0].document_name == "HRPolicy.pdf"
    assert chunks[1].chunk_id == "hrpolicy-p2-c1"


def test_chunking_service_uses_overlap() -> None:
    chunking_service = ChunkingService(chunk_size=10, overlap=3)

    chunks = chunking_service._chunk_text("abcdefghijklmno")

    assert chunks == ["abcdefghij", "hijklmno"]
