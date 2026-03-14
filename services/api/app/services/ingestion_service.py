from pathlib import Path

from app.core.config import Settings
from app.core.logging import get_logger
from app.domain.models import ChunkInput, ReindexResult
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.openai_service import OpenAIService
from app.services.pdf_extraction_service import PDFExtractionService
from app.services.search_index_service import SearchIndexService
from app.services.search_service import SearchService

logger = get_logger(__name__)


class IngestionService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.openai_service = OpenAIService(settings)
        self.embedding_service = EmbeddingService(self.openai_service)
        self.search_index_service = SearchIndexService(SearchService(settings))
        self.pdf_extraction_service = PDFExtractionService()
        self.chunking_service = ChunkingService()

    def reindex_documents(self, file_paths: list[Path]) -> ReindexResult:
        all_chunks: list[ChunkInput] = []
        chunks_by_document: dict[str, int] = {}

        for file_path in file_paths:
            chunks = self.extract_chunks(file_path)
            all_chunks.extend(chunks)
            chunks_by_document[file_path.name] = len(chunks)

        if not all_chunks:
            self.search_index_service.clear_index()
            return ReindexResult(indexed_documents=0, indexed_chunks=0, chunks_by_document={})

        vectors = self.embedding_service.embed_batch([chunk.content for chunk in all_chunks])
        self.search_index_service.rebuild_index(all_chunks, vectors)
        logger.info("reindex_complete documents=%s chunks=%s", len(file_paths), len(all_chunks))
        return ReindexResult(
            indexed_documents=len(file_paths),
            indexed_chunks=len(all_chunks),
            chunks_by_document=chunks_by_document,
        )

    def extract_chunks(self, file_path: Path) -> list[ChunkInput]:
        pages = self.pdf_extraction_service.extract_pages(file_path)
        chunks = self.chunking_service.chunk_pages(pages)
        logger.info("extracted_chunks document=%s chunks=%s", file_path.name, len(chunks))
        return chunks
