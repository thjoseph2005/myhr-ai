from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
import json

from app.core.config import Settings, get_settings
from app.domain.models import IndexedDocument
from app.schemas.documents import DocumentInfo, DocumentStatusResponse, ReindexResponse
from app.services.folder_scanning_service import FolderScanningService
from app.services.ingestion_service import IngestionService

INDEX_STATE_FILENAME = ".index_state.json"


class DocumentService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.knowledge_base_path = Path(settings.knowledge_base_path)
        self.ingestion_service = IngestionService(settings)
        self.folder_scanning_service = FolderScanningService(self.knowledge_base_path)
        self.state_file_path = self.knowledge_base_path / INDEX_STATE_FILENAME

    def get_status(self) -> DocumentStatusResponse:
        discovered_documents = self._discover_documents()
        state = self._read_state()
        indexed_documents = state.get("indexed_documents", {})
        total_indexed_chunks = int(state.get("total_indexed_chunks", 0))
        return DocumentStatusResponse(
            knowledge_base_path=str(self.knowledge_base_path),
            discovered_documents=[
                DocumentInfo(
                    document_id=document.document_id,
                    document_name=document.document_name,
                    path=document.path,
                    indexed=document.document_name in indexed_documents,
                    indexed_chunks=int(indexed_documents.get(document.document_name, 0)),
                )
                for document in discovered_documents
            ],
            indexing_status=state.get("indexing_status", "not_started"),
            last_indexed_at=state.get("last_indexed_at"),
            indexed_document_count=int(state.get("indexed_document_count", 0)),
            total_indexed_chunks=total_indexed_chunks,
            azure_enabled=self.settings.azure_enabled,
        )

    def reindex(self) -> ReindexResponse:
        documents = self._discover_documents()
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
        self._write_state(
            {
                "indexing_status": "indexing",
                "last_indexed_at": None,
                "indexed_document_count": 0,
                "total_indexed_chunks": 0,
                "indexed_documents": {},
            }
        )

        try:
            result = self.ingestion_service.reindex_documents(
                [Path(document.path) for document in documents]
            )
            indexed_at = datetime.now(UTC).isoformat()
            self._write_state(
                {
                    "indexing_status": "completed",
                    "last_indexed_at": indexed_at,
                    "indexed_document_count": result.indexed_documents,
                    "total_indexed_chunks": result.indexed_chunks,
                    "indexed_documents": result.chunks_by_document,
                }
            )
            return ReindexResponse(
                indexed_documents=result.indexed_documents,
                indexed_chunks=result.indexed_chunks,
                indexing_status="completed",
                last_indexed_at=indexed_at,
            )
        except Exception:
            self._write_state(
                {
                    "indexing_status": "error",
                    "last_indexed_at": None,
                    "indexed_document_count": 0,
                    "total_indexed_chunks": 0,
                    "indexed_documents": {},
                }
            )
            raise

    def _discover_documents(self) -> list[IndexedDocument]:
        return self.folder_scanning_service.discover_documents()

    def _read_state(self) -> dict[str, object]:
        if not self.state_file_path.exists():
            return {}
        return json.loads(self.state_file_path.read_text(encoding="utf-8"))

    def _write_state(self, state: dict[str, object]) -> None:
        self.state_file_path.write_text(json.dumps(state, indent=2), encoding="utf-8")


@lru_cache
def get_document_service() -> DocumentService:
    return DocumentService(get_settings())
