from dataclasses import dataclass
import re


@dataclass(slots=True)
class SQLQueryPlan:
    intent: str
    sql: str
    parameters: list[str]
    description: str


class SQLQueryBuilderService:
    def build(self, question: str) -> SQLQueryPlan | None:
        normalized = " ".join(question.lower().split())
        collapsed = normalized.replace(" ", "")

        if self._is_total_employee_count_question(normalized, collapsed):
            return self._total_employee_count()
        if self._is_total_department_count_question(normalized, collapsed):
            return self._total_department_count()
        if self._is_department_headcount_summary_question(normalized, collapsed):
            return self._department_headcount_summary()

        patterns: list[tuple[str, str, callable]] = [
            (
                "department_headcount",
                r"how many .*?(?:in|are in) (?:the )?([a-z &]+?)(?: department)?$",
                self._department_headcount,
            ),
            (
                "department_members",
                r"(?:who|which employees) .*?(?:in|works in|are in) (?:the )?([a-z &]+?)(?: department)?$",
                self._department_members,
            ),
            (
                "department_leader",
                r"who (?:leads|heads|manages) (?:the )?([a-z &]+?)(?: department)?$",
                self._department_leader,
            ),
            (
                "employee_manager",
                r"who (?:is )?(.+?)'?s manager$",
                self._employee_manager,
            ),
            (
                "employee_reports_to",
                r"who does (.+?) report to$",
                self._employee_manager,
            ),
            (
                "employee_department",
                r"what department is (.+?) in$",
                self._employee_department,
            ),
            (
                "employee_title",
                r"what is (.+?)'?s title$",
                self._employee_title,
            ),
            (
                "employee_email",
                r"what is (.+?)'?s email$",
                self._employee_email,
            ),
            (
                "employee_location",
                r"where is (.+?) based$",
                self._employee_location,
            ),
            (
                "employee_profile",
                r"tell me about (.+)$",
                self._employee_profile,
            ),
        ]

        for _, pattern, builder in patterns:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)
            if match:
                value = match.group(1).strip() if match.lastindex else ""
                return builder(value)

        return None

    def _total_employee_count(self) -> SQLQueryPlan:
        return SQLQueryPlan(
            intent="total_employee_count",
            sql="SELECT COUNT(*) AS employee_count FROM employees",
            parameters=[],
            description="Total employee count",
        )

    def _total_department_count(self) -> SQLQueryPlan:
        return SQLQueryPlan(
            intent="total_department_count",
            sql="SELECT COUNT(*) AS department_count FROM departments",
            parameters=[],
            description="Total department count",
        )

    def _department_headcount_summary(self) -> SQLQueryPlan:
        return SQLQueryPlan(
            intent="department_headcount_summary",
            sql=(
                "SELECT d.name AS department_name, COUNT(e.employee_id) AS employee_count "
                "FROM departments d "
                "LEFT JOIN employees e ON e.department_id = d.department_id "
                "GROUP BY d.department_id, d.name "
                "ORDER BY d.name"
            ),
            parameters=[],
            description="Employee count by department",
        )

    @staticmethod
    def _is_total_employee_count_question(normalized: str, collapsed: str) -> bool:
        natural_patterns = [
            r"(?:get|what is|show|give me)? ?(?:the )?(?:(?:total )?(?:count of )|(?:total count of )|(?:number of )|(?:total number of ))employees?\??$",
            r"how many employees (?:are there|do we have|exist)(?: in (?:the|this) company)?\??$",
            r"(?:what is|show|give me)? ?(?:the )?company headcount\??$",
        ]
        collapsed_patterns = [
            r"howmanyemployees(?:arethere|dowehave|exist)(?:inthecompany|inthiscompany)?\??$",
            r"(?:whatis|show|giveme)?(?:the)?companyheadcount\??$",
        ]

        return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in natural_patterns) or any(
            re.search(pattern, collapsed, flags=re.IGNORECASE) for pattern in collapsed_patterns
        )

    @staticmethod
    def _is_total_department_count_question(normalized: str, collapsed: str) -> bool:
        natural_patterns = [
            r"(?:get|what is|show|give me)? ?(?:the )?(?:(?:total )?(?:count of )|(?:total count of )|(?:number of )|(?:total number of ))departments?\??$",
            r"how many departments (?:are there|do we have|exist|in the company)?\??$",
        ]
        collapsed_patterns = [
            r"howmanydepartments(?:arethere|dowehave|exist|inthecompany)?\??$",
        ]

        return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in natural_patterns) or any(
            re.search(pattern, collapsed, flags=re.IGNORECASE) for pattern in collapsed_patterns
        )

    @staticmethod
    def _is_department_headcount_summary_question(normalized: str, collapsed: str) -> bool:
        natural_patterns = [
            r"(?:give me|show|what is|what are|list)? ?(?:the )?(?:count|counts|headcount|headcounts|number) of employees by departments?\??$",
            r"(?:give me|show|what is|what are|list)? ?employees by departments?\??$",
            r"(?:give me|show|what is|what are|list)? ?(?:department|departments) (?:employee )?(?:count|counts|headcount|headcounts|summary|breakdown)\??$",
            r"(?:give me|show|what is|what are|list)? ?(?:employee )?(?:count|counts|headcount|headcounts) by departments?\??$",
        ]
        collapsed_patterns = [
            r"(?:giveme|show|whatis|whatare|list)?(?:the)?(?:count|counts|headcount|headcounts|number)ofemployeesbydepartments?\??$",
            r"(?:giveme|show|whatis|whatare|list)?employeesbydepartments?\??$",
            r"(?:giveme|show|whatis|whatare|list)?departments(?:employee)?(?:count|counts|headcount|headcounts|summary|breakdown)\??$",
            r"(?:giveme|show|whatis|whatare|list)?(?:employee)?(?:count|counts|headcount|headcounts)bydepartments?\??$",
        ]

        return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in natural_patterns) or any(
            re.search(pattern, collapsed, flags=re.IGNORECASE) for pattern in collapsed_patterns
        )

    def _department_members(self, department: str) -> SQLQueryPlan:
        return SQLQueryPlan(
            intent="department_members",
            sql=(
                "SELECT e.first_name || ' ' || e.last_name AS employee_name, e.title, e.location "
                "FROM employees e "
                "JOIN departments d ON e.department_id = d.department_id "
                "WHERE lower(d.name) = lower(?) "
                "ORDER BY e.last_name, e.first_name"
            ),
            parameters=[self._normalize_department(department)],
            description=f"Employees in the {department.title()} department",
        )

    def _department_headcount(self, department: str) -> SQLQueryPlan:
        return SQLQueryPlan(
            intent="department_headcount",
            sql=(
                "SELECT d.name AS department_name, COUNT(*) AS employee_count "
                "FROM employees e "
                "JOIN departments d ON e.department_id = d.department_id "
                "WHERE lower(d.name) = lower(?) "
                "GROUP BY d.name"
            ),
            parameters=[self._normalize_department(department)],
            description=f"Headcount for the {department.title()} department",
        )

    def _department_leader(self, department: str) -> SQLQueryPlan:
        return SQLQueryPlan(
            intent="department_leader",
            sql=(
                "SELECT d.name AS department_name, "
                "leader.first_name || ' ' || leader.last_name AS leader_name, leader.title "
                "FROM departments d "
                "JOIN employees leader ON d.leader_employee_id = leader.employee_id "
                "WHERE lower(d.name) = lower(?)"
            ),
            parameters=[self._normalize_department(department)],
            description=f"Leader for the {department.title()} department",
        )

    def _employee_manager(self, employee_name: str) -> SQLQueryPlan:
        return SQLQueryPlan(
            intent="employee_manager",
            sql=(
                "SELECT e.first_name || ' ' || e.last_name AS employee_name, "
                "manager.first_name || ' ' || manager.last_name AS manager_name, manager.title AS manager_title "
                "FROM employees e "
                "LEFT JOIN employees manager ON e.manager_id = manager.employee_id "
                "WHERE lower(e.first_name || ' ' || e.last_name) = lower(?)"
            ),
            parameters=[self._normalize_employee(employee_name)],
            description=f"Manager lookup for {employee_name.title()}",
        )

    def _employee_department(self, employee_name: str) -> SQLQueryPlan:
        return SQLQueryPlan(
            intent="employee_department",
            sql=(
                "SELECT e.first_name || ' ' || e.last_name AS employee_name, d.name AS department_name, e.title "
                "FROM employees e "
                "JOIN departments d ON e.department_id = d.department_id "
                "WHERE lower(e.first_name || ' ' || e.last_name) = lower(?)"
            ),
            parameters=[self._normalize_employee(employee_name)],
            description=f"Department lookup for {employee_name.title()}",
        )

    def _employee_title(self, employee_name: str) -> SQLQueryPlan:
        return SQLQueryPlan(
            intent="employee_title",
            sql=(
                "SELECT e.first_name || ' ' || e.last_name AS employee_name, e.title, d.name AS department_name "
                "FROM employees e "
                "JOIN departments d ON e.department_id = d.department_id "
                "WHERE lower(e.first_name || ' ' || e.last_name) = lower(?)"
            ),
            parameters=[self._normalize_employee(employee_name)],
            description=f"Title lookup for {employee_name.title()}",
        )

    def _employee_email(self, employee_name: str) -> SQLQueryPlan:
        return SQLQueryPlan(
            intent="employee_email",
            sql=(
                "SELECT e.first_name || ' ' || e.last_name AS employee_name, e.email, e.title "
                "FROM employees e "
                "WHERE lower(e.first_name || ' ' || e.last_name) = lower(?)"
            ),
            parameters=[self._normalize_employee(employee_name)],
            description=f"Email lookup for {employee_name.title()}",
        )

    def _employee_location(self, employee_name: str) -> SQLQueryPlan:
        return SQLQueryPlan(
            intent="employee_location",
            sql=(
                "SELECT e.first_name || ' ' || e.last_name AS employee_name, e.location, e.title "
                "FROM employees e "
                "WHERE lower(e.first_name || ' ' || e.last_name) = lower(?)"
            ),
            parameters=[self._normalize_employee(employee_name)],
            description=f"Location lookup for {employee_name.title()}",
        )

    def _employee_profile(self, employee_name: str) -> SQLQueryPlan:
        return SQLQueryPlan(
            intent="employee_profile",
            sql=(
                "SELECT e.first_name || ' ' || e.last_name AS employee_name, e.title, d.name AS department_name, "
                "e.location, e.employment_type, e.start_date "
                "FROM employees e "
                "JOIN departments d ON e.department_id = d.department_id "
                "WHERE lower(e.first_name || ' ' || e.last_name) = lower(?)"
            ),
            parameters=[self._normalize_employee(employee_name)],
            description=f"Profile lookup for {employee_name.title()}",
        )

    @staticmethod
    def _normalize_department(value: str) -> str:
        return " ".join(part.capitalize() for part in value.split())

    @staticmethod
    def _normalize_employee(value: str) -> str:
        return " ".join(part.capitalize() for part in value.split())
