from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.chat import Citation


class SupervisorAgentOutput(BaseModel):
    selected_tool: Literal["policy_search_tool", "hr_sql_tool"]
    answer: str = Field(min_length=1)
    grounded: bool
    citations: list[Citation] = Field(default_factory=list)
    rationale: str = Field(default="")
