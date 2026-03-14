from app.services.openai_service import OpenAIService


class EmbeddingService:
    def __init__(self, openai_service: OpenAIService) -> None:
        self.openai_service = openai_service

    def embed_text(self, text: str) -> list[float]:
        return self.openai_service.embed_text(text)

    def embed_batch(self, values: list[str]) -> list[list[float]]:
        return [self.embed_text(value) for value in values]
