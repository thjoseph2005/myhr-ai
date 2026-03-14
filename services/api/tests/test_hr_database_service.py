from pathlib import Path

from app.core.config import Settings
from app.services.hr_database_service import HRDatabaseService


def build_settings(tmp_path: Path) -> Settings:
    return Settings(
        APP_ENV="test",
        LOG_LEVEL="INFO",
        API_CORS_ORIGINS=["http://localhost:3000"],
        KNOWLEDGE_BASE_PATH=str(tmp_path / "knowledge_base"),
        HR_DATABASE_PATH=str(tmp_path / "hr.sqlite3"),
        MOCK_AZURE_MODE=True,
    )


def test_seeds_hr_database_and_returns_employee_rows(tmp_path: Path) -> None:
    service = HRDatabaseService(build_settings(tmp_path))
    service.ensure_database(force_reset=True)

    rows = service.execute_select(
        "SELECT first_name, last_name FROM employees WHERE lower(last_name) = lower(?)",
        ["Lee"],
    )

    assert rows[0]["first_name"] == "Marcus"
    assert rows[0]["last_name"] == "Lee"
