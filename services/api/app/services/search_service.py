from pathlib import Path
import json
import math

from azure.search.documents.models import VectorizedQuery
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

from app.core.config import Settings
from app.domain.models import ChunkInput, RetrievedChunk
from app.infrastructure.azure_clients import build_search_client, build_search_index_client

MOCK_INDEX_FILENAME = ".mock_index.json"


class SearchService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.index_file_path = Path(settings.knowledge_base_path) / MOCK_INDEX_FILENAME
        self.search_client = build_search_client(settings) if settings.azure_enabled else None
        self.search_index_client = (
            build_search_index_client(settings) if settings.azure_enabled else None
        )

    def rebuild_index(self, chunks: list[ChunkInput], vectors: list[list[float]]) -> None:
        if not chunks:
            self.clear_index()
            return

        if self.settings.azure_enabled:
            self._rebuild_azure_index(chunks, vectors)
            return

        documents = [
            {
                "id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "document_name": chunk.document_name,
                "page_number": chunk.page_number,
                "chunk_number": chunk.chunk_number,
                "content": chunk.content,
                "content_vector": vector,
            }
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        self.index_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_file_path.write_text(json.dumps(documents), encoding="utf-8")

    def clear_index(self) -> None:
        if self.settings.azure_enabled:
            assert self.search_index_client is not None
            existing = [index.name for index in self.search_index_client.list_indexes()]
            if self.settings.azure_search_index_name in existing:
                self.search_index_client.delete_index(self.settings.azure_search_index_name)
            return

        if self.index_file_path.exists():
            self.index_file_path.unlink()

    def search(self, query: str, vector: list[float], top_k: int) -> list[RetrievedChunk]:
        if self.settings.azure_enabled:
            return self._search_azure(query, vector, top_k)
        return self._search_mock(query, vector, top_k)

    def _rebuild_azure_index(self, chunks: list[ChunkInput], vectors: list[list[float]]) -> None:
        assert self.search_client is not None
        assert self.search_index_client is not None

        index_name = self.settings.azure_search_index_name
        existing = [index.name for index in self.search_index_client.list_indexes()]
        if index_name in existing:
            self.search_index_client.delete_index(index_name)

        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SimpleField(name="document_id", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="document_name", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="page_number", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
            SimpleField(name="chunk_number", type=SearchFieldDataType.Int32, sortable=True),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=len(vectors[0]),
                vector_search_profile_name="default-vector-profile",
            ),
        ]
        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="default-hnsw")],
            profiles=[
                VectorSearchProfile(
                    name="default-vector-profile",
                    algorithm_configuration_name="default-hnsw",
                )
            ],
        )
        self.search_index_client.create_index(
            SearchIndex(name=index_name, fields=fields, vector_search=vector_search)
        )

        documents = [
            {
                "id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "document_name": chunk.document_name,
                "page_number": chunk.page_number,
                "chunk_number": chunk.chunk_number,
                "content": chunk.content,
                "content_vector": vector,
            }
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        self.search_client.upload_documents(documents=documents)

    def _search_azure(self, query: str, vector: list[float], top_k: int) -> list[RetrievedChunk]:
        assert self.search_client is not None

        vector_query = VectorizedQuery(
            vector=vector,
            k_nearest_neighbors=top_k,
            fields="content_vector",
        )
        results = self.search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            top=top_k,
            select=["id", "document_id", "document_name", "page_number", "content"],
        )
        return [
            RetrievedChunk(
                chunk_id=str(item["id"]),
                document_id=str(item["document_id"]),
                document_name=str(item["document_name"]),
                page_number=int(item["page_number"]),
                content=str(item["content"]),
                score=float(item["@search.score"]),
            )
            for item in results
        ]

    def _search_mock(self, query: str, vector: list[float], top_k: int) -> list[RetrievedChunk]:
        if not self.index_file_path.exists():
            return []

        lowered_terms = {term for term in query.lower().split() if term}
        documents = json.loads(self.index_file_path.read_text(encoding="utf-8"))
        scored_documents: list[RetrievedChunk] = []
        for item in documents:
            content = str(item["content"])
            lexical_score = sum(1 for term in lowered_terms if term in content.lower())
            vector_score = self._cosine_similarity(vector, list(item.get("content_vector", [])))
            score = lexical_score + vector_score
            if score <= 0:
                continue
            scored_documents.append(
                RetrievedChunk(
                    chunk_id=str(item["id"]),
                    document_id=str(item["document_id"]),
                    document_name=str(item["document_name"]),
                    page_number=int(item["page_number"]),
                    content=content,
                    score=score,
                )
            )

        scored_documents.sort(key=lambda chunk: chunk.score, reverse=True)
        return scored_documents[:top_k]

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        numerator = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)
