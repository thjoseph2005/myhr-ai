from pydantic import BaseModel, Field


class HybridQuestionPlan(BaseModel):
    policy_question: str = Field(default="")
    structured_question: str = Field(default="")
    reason: str = Field(default="")
