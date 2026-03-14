from fastapi import APIRouter, Depends

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import RAGService, get_rag_service

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> ChatResponse:
    return await rag_service.answer_question(payload)
