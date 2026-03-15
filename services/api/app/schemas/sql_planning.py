from pydantic import BaseModel, Field


class SQLPlanDecision(BaseModel):
    intent: str = Field(min_length=1)
    sql: str = Field(min_length=1)
    parameters: list[str] = Field(default_factory=list)
    description: str = Field(min_length=1)
