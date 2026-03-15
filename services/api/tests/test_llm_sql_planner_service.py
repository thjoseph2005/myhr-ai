from pathlib import Path

from app.core.config import Settings
from app.services.hr_database_service import HRDatabaseService
from app.services.llm_sql_planner_service import LLMSQLPlannerService


class FakeOpenAIService:
    def __init__(self, response: str, azure_enabled: bool = True) -> None:
        self._response = response
        self.settings = type("SettingsStub", (), {"azure_enabled": azure_enabled})()

    def generate_json(self, _: list[dict[str, str]]) -> str:
        return self._response


class RaisingOpenAIService:
    def __init__(self, azure_enabled: bool = True) -> None:
        self.settings = type("SettingsStub", (), {"azure_enabled": azure_enabled})()

    def generate_json(self, _: list[dict[str, str]]) -> str:
        raise RuntimeError("planner unavailable")


def build_settings(tmp_path: Path) -> Settings:
    return Settings(
        APP_ENV="test",
        LOG_LEVEL="INFO",
        API_CORS_ORIGINS=["http://localhost:3000"],
        KNOWLEDGE_BASE_PATH=str(tmp_path / "knowledge_base"),
        HR_DATABASE_PATH=str(tmp_path / "hr.sqlite3"),
        MOCK_AZURE_MODE=True,
    )


def test_builds_sql_plan_from_llm_json(tmp_path: Path) -> None:
    hr_database_service = HRDatabaseService(build_settings(tmp_path))
    planner = LLMSQLPlannerService(
        FakeOpenAIService(
            '{"intent":"company_headcount","sql":"SELECT COUNT(*) AS employee_count FROM employees","parameters":[],"description":"Company headcount"}'
        ),
        hr_database_service,
    )

    plan = planner.build("How many employees are there in the company?")

    assert plan is not None
    assert plan.intent == "company_headcount"
    assert "COUNT(*)" in plan.sql


def test_returns_none_for_unsupported_llm_plan(tmp_path: Path) -> None:
    hr_database_service = HRDatabaseService(build_settings(tmp_path))
    planner = LLMSQLPlannerService(
        FakeOpenAIService(
            '{"intent":"unsupported","sql":"","parameters":[],"description":"Unsupported question"}'
        ),
        hr_database_service,
    )

    plan = planner.build("Explain the company culture.")

    assert plan is None


def test_returns_none_when_llm_sql_planner_raises(tmp_path: Path) -> None:
    hr_database_service = HRDatabaseService(build_settings(tmp_path))
    planner = LLMSQLPlannerService(
        RaisingOpenAIService(),
        hr_database_service,
    )

    plan = planner.build("How many departments are there?")

    assert plan is None


def test_builds_company_managers_plan_from_llm_json(tmp_path: Path) -> None:
    hr_database_service = HRDatabaseService(build_settings(tmp_path))
    planner = LLMSQLPlannerService(
        FakeOpenAIService(
            '{"intent":"company_managers","sql":"SELECT DISTINCT manager.employee_id, manager.first_name || \' \' || manager.last_name AS manager_name, manager.title, d.name AS department_name FROM employees e JOIN employees manager ON e.manager_id = manager.employee_id LEFT JOIN departments d ON manager.department_id = d.department_id ORDER BY manager.last_name, manager.first_name","parameters":[],"description":"Managers in the company"}'
        ),
        hr_database_service,
    )

    plan = planner.build("Who are the managers of this company?")

    assert plan is not None
    assert plan.intent == "company_managers"
    assert "DISTINCT" in plan.sql
