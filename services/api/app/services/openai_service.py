import hashlib

from app.core.config import Settings
from app.infrastructure.azure_clients import build_openai_client


class OpenAIService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = build_openai_client(settings) if settings.azure_enabled else None

    def embed_text(self, text: str) -> list[float]:
        if not self.settings.azure_enabled:
            return self._mock_embedding(text)

        assert self.client is not None
        response = self.client.embeddings.create(
            model=self.settings.azure_openai_embedding_deployment,
            input=text,
        )
        return list(response.data[0].embedding)

    def generate_answer(self, messages: list[dict[str, str]]) -> str:
        if not self.settings.azure_enabled:
            user_message = messages[-1]["content"]
            context_start = user_message.find("Context:\n")
            context = user_message[context_start + len("Context:\n") :] if context_start >= 0 else ""
            for block in context.split("\n\n"):
                if ": " in block:
                    return block.split(": ", maxsplit=1)[1].strip()
            return ""

        assert self.client is not None
        response = self.client.chat.completions.create(
            model=self.settings.azure_openai_chat_deployment,
            temperature=self.settings.default_chat_temperature,
            messages=messages,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""

    @staticmethod
    def _mock_embedding(text: str, dimensions: int = 12) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [digest[index] / 255 for index in range(dimensions)]
