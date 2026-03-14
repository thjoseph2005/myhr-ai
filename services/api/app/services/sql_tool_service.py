from app.services.hr_database_service import HRDatabaseService
from app.services.sql_safety_service import SQLSafetyService
from app.services.sql_query_builder_service import SQLQueryPlan


class SQLToolService:
    def __init__(self, hr_database_service: HRDatabaseService) -> None:
        self.hr_database_service = hr_database_service
        self.sql_safety_service = SQLSafetyService()

    def run_query(self, plan: SQLQueryPlan) -> list[dict[str, object]]:
        self.sql_safety_service.validate(plan.sql)
        return self.hr_database_service.execute_select(plan.sql, plan.parameters)
