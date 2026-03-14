NOT_FOUND_MESSAGE = "I could not find this in the HR policy document."


class GroundingEvaluatorService:
    def is_grounded(self, answer: str) -> bool:
        lowered = answer.lower()
        unsupported_markers = [
            NOT_FOUND_MESSAGE.lower(),
            "not provided in the context",
            "insufficient information",
        ]
        return bool(answer.strip()) and not any(marker in lowered for marker in unsupported_markers)
