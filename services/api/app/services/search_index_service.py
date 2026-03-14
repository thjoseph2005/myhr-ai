from app.domain.models import ChunkInput
from app.services.search_service import SearchService


class SearchIndexService:
    def __init__(self, search_service: SearchService) -> None:
        self.search_service = search_service

    def rebuild_index(self, chunks: list[ChunkInput], vectors: list[list[float]]) -> None:
        self.search_service.rebuild_index(chunks, vectors)

    def clear_index(self) -> None:
        self.search_service.clear_index()
