from app.services.structured_answer_service import StructuredAnswerService
from app.services.sql_query_builder_service import SQLQueryPlan


class FakeAnswerGenerationService:
    def __init__(self, answer: str, azure_enabled: bool = True) -> None:
        self.answer = answer
        self.openai_service = type(
            "OpenAIStub",
            (),
            {"settings": type("SettingsStub", (), {"azure_enabled": azure_enabled})()},
        )()

    def generate_answer(self, _: list[dict[str, str]]) -> str:
        return self.answer


class FakeGroundingEvaluatorService:
    def is_grounded(self, answer: str) -> bool:
        return bool(answer.strip()) and "could not find" not in answer.lower()


def test_uses_llm_to_structure_sql_answer_when_available() -> None:
    service = StructuredAnswerService(
        FakeAnswerGenerationService("The company currently has 12 employees."),
        FakeGroundingEvaluatorService(),
    )

    answer, citations, grounded = service.build_answer(
        SQLQueryPlan(
            intent="total_employee_count",
            sql="SELECT COUNT(*) AS employee_count FROM employees",
            parameters=[],
            description="Total employee count",
        ),
        [{"employee_count": 12}],
        "How many employees are there in this company?",
    )

    assert grounded is True
    assert answer == "The company currently has 12 employees."
    assert citations[0].document_name == "HR Database"


def test_falls_back_to_template_when_llm_is_unavailable() -> None:
    service = StructuredAnswerService(
        FakeAnswerGenerationService("", azure_enabled=False),
        FakeGroundingEvaluatorService(),
    )

    answer, citations, grounded = service.build_answer(
        SQLQueryPlan(
            intent="total_employee_count",
            sql="SELECT COUNT(*) AS employee_count FROM employees",
            parameters=[],
            description="Total employee count",
        ),
        [{"employee_count": 12}],
        "How many employees are there in this company?",
    )

    assert grounded is True
    assert answer == "There are 12 employees in the HR database."
    assert citations[0].document_name == "HR Database"
