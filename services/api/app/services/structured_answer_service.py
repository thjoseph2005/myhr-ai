import json

from app.schemas.chat import Citation
from app.services.answer_generation_service import AnswerGenerationService
from app.services.grounding_evaluator_service import GroundingEvaluatorService, NOT_FOUND_MESSAGE
from app.services.sql_query_builder_service import SQLQueryPlan

STRUCTURED_ANSWER_SYSTEM_PROMPT = """You are an HR assistant formatting answers from structured HR database results.

Rules:
- Use only the supplied SQL result rows and metadata.
- Do not invent facts, names, counts, or fields.
- Write in a polished, enterprise-professional tone.
- Prefer natural language over rigid database phrasing.
- Keep answers concise, clear, and confident.
- When the result is a count or summary, phrase it in a business-friendly way.
- When the result is about a person or department, answer directly in one or two sentences.
- If the rows do not support an answer, reply exactly:
I could not find this in the HR policy document.
"""


class StructuredAnswerService:
    def __init__(
        self,
        answer_generation_service: AnswerGenerationService,
        grounding_evaluator_service: GroundingEvaluatorService,
    ) -> None:
        self.answer_generation_service = answer_generation_service
        self.grounding_evaluator_service = grounding_evaluator_service

    def build_answer(
        self,
        plan: SQLQueryPlan,
        rows: list[dict[str, object]],
        question: str,
    ) -> tuple[str, list[Citation], bool]:
        if not rows:
            return NOT_FOUND_MESSAGE, [], False

        citations = [
            Citation(
                document_id="hr_database",
                document_name="HR Database",
                page_number=0,
                chunk_id=f"sql:{plan.intent}",
                excerpt=plan.description,
            )
        ]

        llm_answer = self._generate_llm_answer(plan, rows, question)
        if llm_answer is not None:
            grounded = self.grounding_evaluator_service.is_grounded(llm_answer)
            if grounded:
                return llm_answer, citations, True

        answer = self._format_answer(plan, rows)
        return answer, citations, True

    def _generate_llm_answer(
        self,
        plan: SQLQueryPlan,
        rows: list[dict[str, object]],
        question: str,
    ) -> str | None:
        openai_service = getattr(self.answer_generation_service, "openai_service", None)
        if not getattr(getattr(openai_service, "settings", None), "azure_enabled", False):
            return None

        messages = [
            {"role": "system", "content": STRUCTURED_ANSWER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n"
                    f"SQL intent: {plan.intent}\n"
                    f"Description: {plan.description}\n"
                    f"Rows: {json.dumps(rows, default=str)}\n\n"
                    "Write a natural-language answer using only these rows."
                ),
            },
        ]
        try:
            return self.answer_generation_service.generate_answer(messages)
        except Exception:
            return None

    def _format_answer(self, plan: SQLQueryPlan, rows: list[dict[str, object]]) -> str:
        if plan.intent == "total_department_count":
            row = rows[0]
            return f"There are {row['department_count']} departments in the HR database."

        if plan.intent == "total_employee_count":
            row = rows[0]
            return f"There are {row['employee_count']} employees in the HR database."

        if plan.intent == "department_members":
            members = ", ".join(
                f"{row['employee_name']} ({row['title']}, {row['location']})" for row in rows
            )
            return f"{plan.description}: {members}."

        if plan.intent == "department_headcount":
            row = rows[0]
            return f"{row['department_name']} has {row['employee_count']} employees in the HR database."

        if plan.intent == "department_headcount_summary":
            breakdown = ", ".join(
                f"{row['department_name']}: {row['employee_count']}" for row in rows
            )
            return f"Employee count by department: {breakdown}."

        if plan.intent == "department_leader":
            row = rows[0]
            return (
                f"{row['leader_name']} leads the {row['department_name']} department "
                f"and serves as {row['title']}."
            )

        if plan.intent == "employee_manager":
            row = rows[0]
            manager_name = row.get("manager_name")
            if manager_name:
                return f"{row['employee_name']}'s manager is {manager_name}, {row['manager_title']}."
            return f"{row['employee_name']} does not have a manager listed in the HR database."

        if plan.intent == "employee_department":
            row = rows[0]
            return f"{row['employee_name']} works in {row['department_name']} as {row['title']}."

        if plan.intent == "employee_title":
            row = rows[0]
            return f"{row['employee_name']}'s title is {row['title']} in {row['department_name']}."

        if plan.intent == "employee_email":
            row = rows[0]
            return f"{row['employee_name']}'s email address is {row['email']}."

        if plan.intent == "employee_location":
            row = rows[0]
            return f"{row['employee_name']} is based in {row['location']} and works as {row['title']}."

        if plan.intent == "employee_profile":
            row = rows[0]
            return (
                f"{row['employee_name']} is a {row['employment_type']} {row['title']} in "
                f"{row['department_name']}, based in {row['location']}, with a start date of "
                f"{row['start_date']}."
            )

        return NOT_FOUND_MESSAGE
