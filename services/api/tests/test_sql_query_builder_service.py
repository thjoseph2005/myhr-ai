from app.services.sql_query_builder_service import SQLQueryBuilderService


def test_builds_total_employee_count_query() -> None:
    service = SQLQueryBuilderService()

    plan = service.build("get the count of Total employee")

    assert plan is not None
    assert plan.intent == "total_employee_count"
    assert plan.parameters == []


def test_builds_total_department_count_query() -> None:
    service = SQLQueryBuilderService()

    plan = service.build("get total count of departments")

    assert plan is not None
    assert plan.intent == "total_department_count"
    assert plan.parameters == []


def test_builds_total_department_count_query_from_natural_question() -> None:
    service = SQLQueryBuilderService()

    plan = service.build("How many departments are there?")

    assert plan is not None
    assert plan.intent == "total_department_count"
    assert plan.parameters == []


def test_builds_total_department_count_query_from_split_word_question() -> None:
    service = SQLQueryBuilderService()

    plan = service.build("How many depart ments are there?")

    assert plan is not None
    assert plan.intent == "total_department_count"
    assert plan.parameters == []


def test_builds_department_headcount_summary_query() -> None:
    service = SQLQueryBuilderService()

    plan = service.build("Give me the count of employees by department")

    assert plan is not None
    assert plan.intent == "department_headcount_summary"
    assert plan.parameters == []


def test_builds_department_members_query() -> None:
    service = SQLQueryBuilderService()

    plan = service.build("Who is in the Finance department?")

    assert plan is not None
    assert plan.intent == "department_members"
    assert plan.parameters == ["Finance"]


def test_builds_employee_manager_query() -> None:
    service = SQLQueryBuilderService()

    plan = service.build("Who is Priya Nair's manager")

    assert plan is not None
    assert plan.intent == "employee_manager"
    assert plan.parameters == ["Priya Nair"]
