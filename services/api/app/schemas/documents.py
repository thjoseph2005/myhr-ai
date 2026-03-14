from pydantic import BaseModel


class DocumentInfo(BaseModel):
    document_id: str
    document_name: str
    path: str
    indexed: bool
    indexed_chunks: int


class DocumentStatusResponse(BaseModel):
    knowledge_base_path: str
    discovered_documents: list[DocumentInfo]
    indexing_status: str
    last_indexed_at: str | None
    indexed_document_count: int
    total_indexed_chunks: int
    azure_enabled: bool


class ReindexResponse(BaseModel):
    indexed_documents: int
    indexed_chunks: int
    indexing_status: str
    last_indexed_at: str | None
