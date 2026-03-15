class IntentRouterService:
    STRUCTURED_KEYWORDS = [
        "department",
        "employee",
        "employees",
        "manager",
        "count",
        "total employee",
        "total employees",
        "reports to",
        "report to",
        "title",
        "email",
        "headcount",
        "based",
        "who leads",
        "who heads",
        "who is",
        "tell me about",
    ]

    POLICY_KEYWORDS = [
        "policy",
        "pto",
        "vacation",
        "leave",
        "holiday",
        "work from home",
        "remote work",
        "benefit",
        "handbook",
        "carryover",
    ]

    def route(self, question: str) -> str:
        normalized = " ".join(question.lower().split())
        collapsed = normalized.replace(" ", "")
        if any(keyword in normalized for keyword in self.POLICY_KEYWORDS):
            return "policy_rag"
        if any(keyword in normalized for keyword in self.STRUCTURED_KEYWORDS):
            return "structured_hr"
        if any(keyword.replace(" ", "") in collapsed for keyword in self.STRUCTURED_KEYWORDS):
            return "structured_hr"
        return "policy_rag"
