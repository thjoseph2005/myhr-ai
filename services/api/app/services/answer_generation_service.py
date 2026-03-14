from app.services.openai_service import OpenAIService


class AnswerGenerationService:
    def __init__(self, openai_service: OpenAIService) -> None:
        self.openai_service = openai_service

    def generate_answer(self, messages: list[dict[str, str]]) -> str:
        return self.openai_service.generate_answer(messages)
