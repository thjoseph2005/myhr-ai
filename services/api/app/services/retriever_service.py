from app.domain.models import RetrievedChunk
from app.services.embedding_service import EmbeddingService
from app.services.search_service import SearchService


class RetrieverService:
    def __init__(self, embedding_service: EmbeddingService, search_service: SearchService) -> None:
        self.embedding_service = embedding_service
        self.search_service = search_service

    def retrieve(self, question: str, top_k: int) -> list[RetrievedChunk]:
        query_vector = self.embedding_service.embed_text(question)
        return self.search_service.search(question, query_vector, top_k)
