from dataclasses import dataclass

from app.schemas.chat import Citation


@dataclass(slots=True)
class AgentExecutionResult:
    answer: str
    citations: list[Citation]
    grounded: bool
    tool_name: str
