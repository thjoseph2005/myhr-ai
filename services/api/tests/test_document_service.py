from pathlib import Path

from app.core.config import Settings
from app.services.document_service import DocumentService


def build_settings(tmp_path: Path) -> Settings:
    return Settings(
        APP_ENV="test",
        LOG_LEVEL="INFO",
        API_CORS_ORIGINS=["http://localhost:3000"],
        KNOWLEDGE_BASE_PATH=str(tmp_path),
        MOCK_AZURE_MODE=True,
    )


def test_discovers_pdf_files_in_knowledge_base(tmp_path: Path) -> None:
    (tmp_path / "EmployeeHandbook.pdf").write_bytes(b"pdf")
    (tmp_path / "LeavePolicy.PDF").write_bytes(b"pdf")
    (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")

    service = DocumentService(build_settings(tmp_path))

    documents = service.get_status().discovered_documents

    assert [document.document_name for document in documents] == [
        "EmployeeHandbook.pdf",
        "LeavePolicy.PDF",
    ]
    assert documents[0].document_id == "employeehandbook"
    assert documents[0].indexed is False
    assert documents[0].indexed_chunks == 0
