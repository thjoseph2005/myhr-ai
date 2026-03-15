from app.schemas.chat import Citation
from app.services.grounding_evaluator_service import NOT_FOUND_MESSAGE
from app.services.sql_query_builder_service import SQLQueryPlan


class StructuredAnswerService:
    def build_answer(
        self,
        plan: SQLQueryPlan,
        rows: list[dict[str, object]],
    ) -> tuple[str, list[Citation], bool]:
        if not rows:
            return NOT_FOUND_MESSAGE, [], False

        answer = self._format_answer(plan, rows)
        citations = [
            Citation(
                document_id="hr_database",
                document_name="HR Database",
                page_number=0,
                chunk_id=f"sql:{plan.intent}",
                excerpt=plan.description,
            )
        ]
        return answer, citations, True

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
