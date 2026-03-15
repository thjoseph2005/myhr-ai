import json

from app.services.openai_service import OpenAIService
from app.services.sql_query_builder_service import SQLQueryPlan

SQL_REPAIR_PROMPT = """You repair read-only SQL query plans for a lightweight HR SQLite database.

Rules:
- Use SELECT queries only.
- Keep queries limited to the employees and departments tables.
- Use positional parameter placeholders '?' for user values.
- If the query cannot be safely repaired, respond with:
{"intent":"unsupported","sql":"","parameters":[],"description":"Unsupported question"}

Respond with valid JSON only:
{"intent":"string","sql":"string","parameters":["string"],"description":"string"}
"""


class LLMSQLRepairService:
    def __init__(self, openai_service: OpenAIService) -> None:
        self.openai_service = openai_service

    def repair(self, question: str, plan: SQLQueryPlan, error_message: str) -> SQLQueryPlan | None:
        if not self.openai_service.settings.azure_enabled:
            return None

        messages = [
            {"role": "system", "content": SQL_REPAIR_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n"
                    f"Broken plan: {json.dumps(plan.__dict__)}\n"
                    f"Error: {error_message}\n"
                    "Repair the plan if possible."
                ),
            },
        ]
        try:
            payload = json.loads(self.openai_service.generate_json(messages))
        except Exception:
            return None

        intent = str(payload.get("intent", "")).strip()
        sql = str(payload.get("sql", "")).strip()
        parameters = payload.get("parameters", [])
        description = str(payload.get("description", "")).strip() or plan.description
        if intent == "unsupported" or not sql:
            return None
        if not isinstance(parameters, list):
            parameters = plan.parameters
        return SQLQueryPlan(
            intent=intent or plan.intent,
            sql=sql,
            parameters=[str(item) for item in parameters],
            description=description,
        )
