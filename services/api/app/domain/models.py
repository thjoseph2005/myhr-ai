from dataclasses import dataclass


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    content: str
    score: float


@dataclass(slots=True)
class ChunkInput:
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    chunk_number: int
    content: str


@dataclass(slots=True)
class IndexedDocument:
    document_id: str
    document_name: str
    path: str


@dataclass(slots=True)
class ExtractedPage:
    document_id: str
    document_name: str
    page_number: int
    text: str


@dataclass(slots=True)
class ReindexResult:
    indexed_documents: int
    indexed_chunks: int
    chunks_by_document: dict[str, int]
