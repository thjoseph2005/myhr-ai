from app.domain.models import RetrievedChunk
from app.schemas.chat import ChatRequest

SYSTEM_PROMPT = """You are an HR policy assistant.
Answer only using the supplied policy excerpts.
If the answer is not supported by the excerpts, reply exactly with: I could not find this in the HR policy document.
Keep answers concise and professional.
"""


class PromptBuilderService:
    def build_messages(
        self,
        payload: ChatRequest,
        retrieved: list[RetrievedChunk],
        max_history_messages: int,
    ) -> list[dict[str, str]]:
        excerpts = "\n\n".join(
            f"[{chunk.chunk_id}] Page {chunk.page_number} from {chunk.document_name}: {chunk.content}"
            for chunk in retrieved
        )
        history = payload.history[-max_history_messages:]
        messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(message.model_dump() for message in history)
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Question: {payload.question}\n\n"
                    f"Context:\n{excerpts}\n\n"
                    "Answer the question and rely only on the context above."
                ),
            }
        )
        return messages
