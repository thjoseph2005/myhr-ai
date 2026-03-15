from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list)
    session_id: str | None = Field(default=None, max_length=128)


class Citation(BaseModel):
    document_id: str
    document_name: str
    page_number: int
    chunk_id: str
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    grounded: bool
