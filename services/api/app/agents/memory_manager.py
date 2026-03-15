import json

from app.schemas.chat import ChatMessage
from app.services.answer_generation_service import AnswerGenerationService

MEMORY_SUMMARY_PROMPT = """You maintain concise long-term memory for an HR assistant.

Summarize the conversation in 2-3 short sentences and capture durable facts that would help future turns.
Return valid JSON only:
{"summary":"string","facts":{"key":"value"}}
"""


class AgentMemoryManager:
    def __init__(self, answer_generation_service: AnswerGenerationService) -> None:
        self.answer_generation_service = answer_generation_service

    def update_memory(
        self,
        existing_summary: str | None,
        existing_facts: dict[str, str],
        latest_history: list[ChatMessage],
    ) -> tuple[str | None, dict[str, str]]:
        openai_service = getattr(self.answer_generation_service, "openai_service", None)
        if getattr(getattr(openai_service, "settings", None), "azure_enabled", False):
            messages = [
                {"role": "system", "content": MEMORY_SUMMARY_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Existing summary: {existing_summary or 'none'}\n"
                        f"Existing facts: {json.dumps(existing_facts)}\n"
                        f"Latest history: {json.dumps([message.model_dump() for message in latest_history], default=str)}"
                    ),
                },
            ]
            try:
                payload = json.loads(openai_service.generate_json(messages))
                summary = payload.get("summary") or existing_summary
                facts = payload.get("facts") or existing_facts
                if isinstance(facts, dict):
                    normalized_facts = {str(key): str(value) for key, value in facts.items()}
                else:
                    normalized_facts = existing_facts
                return summary, normalized_facts
            except Exception:
                pass

        summary = latest_history[-1].content if latest_history else existing_summary
        facts = dict(existing_facts)
        if len(latest_history) >= 2:
            facts["last_user_question"] = latest_history[-2].content
            facts["last_assistant_answer"] = latest_history[-1].content
        return summary, facts
