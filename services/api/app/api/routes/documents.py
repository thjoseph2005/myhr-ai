from fastapi import APIRouter, Depends

from app.schemas.documents import DocumentStatusResponse, ReindexResponse
from app.services.document_service import DocumentService, get_document_service

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("/status", response_model=DocumentStatusResponse)
async def document_status(
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentStatusResponse:
    return document_service.get_status()


@router.post("/reindex", response_model=ReindexResponse)
async def reindex_documents(
    document_service: DocumentService = Depends(get_document_service),
) -> ReindexResponse:
    return document_service.reindex()
