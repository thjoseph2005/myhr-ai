import re


class SQLSafetyService:
    FORBIDDEN_PATTERNS = [
        r"\bINSERT\b",
        r"\bUPDATE\b",
        r"\bDELETE\b",
        r"\bDROP\b",
        r"\bALTER\b",
        r"\bCREATE\b",
        r"\bATTACH\b",
        r"\bDETACH\b",
        r"\bPRAGMA\b",
        r"--",
        r";",
    ]

    def validate(self, sql: str) -> None:
        normalized = sql.strip()
        if not normalized.lower().startswith("select"):
            raise ValueError("Only read-only SELECT queries are allowed.")

        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, normalized, flags=re.IGNORECASE):
                raise ValueError("Unsafe SQL pattern detected.")
