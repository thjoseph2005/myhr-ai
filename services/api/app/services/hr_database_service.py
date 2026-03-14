from pathlib import Path
import sqlite3

from app.core.config import Settings


class HRDatabaseService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.database_path = Path(settings.hr_database_path)
        self.seed_script_path = Path(__file__).resolve().parents[4] / "data" / "hr_seed.sql"

    def ensure_database(self, force_reset: bool = False) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        if not force_reset and self.database_path.exists() and self._has_seed_data():
            return

        with sqlite3.connect(self.database_path) as connection:
            connection.executescript(self.seed_script_path.read_text(encoding="utf-8"))
            connection.commit()

    def execute_select(self, sql: str, parameters: list[str] | None = None) -> list[dict[str, object]]:
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.execute(sql, parameters or [])
            rows = cursor.fetchmany(self.settings.sql_max_rows)
            return [dict(row) for row in rows]

    def schema_description(self) -> str:
        return (
            "departments(department_id, name, code, leader_employee_id); "
            "employees(employee_id, first_name, last_name, email, department_id, title, "
            "manager_id, employment_type, location, start_date, status)"
        )

    def _has_seed_data(self) -> bool:
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='employees'"
            )
            if cursor.fetchone() is None:
                return False
            count_cursor = connection.execute("SELECT COUNT(*) FROM employees")
            row = count_cursor.fetchone()
            return bool(row and row[0] > 0)
