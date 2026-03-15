import json

from app.schemas.sql_planning import SQLPlanDecision
from app.services.hr_database_service import HRDatabaseService
from app.services.openai_service import OpenAIService
from app.services.sql_query_builder_service import SQLQueryPlan

SQL_PLANNER_SYSTEM_PROMPT = """You are a SQL planning assistant for a lightweight HR SQLite database.
Generate a read-only SQL plan for the user's question.

Rules:
- Use SELECT queries only.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, ATTACH, DETACH, PRAGMA, comments, or semicolons.
- Prefer exact schema fields only.
- Use positional parameter placeholders '?' instead of inlining user values.
- Keep queries concise and limited to the employees and departments tables.
- If the question cannot be answered from the schema, respond with:
{{"intent":"unsupported","sql":"","parameters":[],"description":"Unsupported question"}}

Schema:
{schema}

Respond with valid JSON only:
{{"intent":"string","sql":"string","parameters":["string"],"description":"string"}}
"""


class LLMSQLPlannerService:
    def __init__(self, openai_service: OpenAIService, hr_database_service: HRDatabaseService) -> None:
        self.openai_service = openai_service
        self.hr_database_service = hr_database_service

    def build(self, question: str) -> SQLQueryPlan | None:
        if not self.openai_service.settings.azure_enabled:
            return None

        messages = [
            {
                "role": "system",
                "content": SQL_PLANNER_SYSTEM_PROMPT.format(
                    schema=self.hr_database_service.schema_description()
                ),
            },
            {"role": "user", "content": question},
        ]
        try:
            content = self.openai_service.generate_json(messages)
            payload = json.loads(content)
            plan = SQLPlanDecision.model_validate(payload)
        except Exception:
            return None

        if plan.intent == "unsupported" or not plan.sql.strip():
            return None

        return SQLQueryPlan(
            intent=plan.intent,
            sql=plan.sql,
            parameters=plan.parameters,
            description=plan.description,
        )
