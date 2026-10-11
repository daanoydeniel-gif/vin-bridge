import time


class ReflectionResult:

    def __init__(
        self,
        success,
        outcome,
        lesson="",
        recommendation="",
        confidence=0.0
    ):
        self.success = bool(success)
        self.outcome = outcome
        self.lesson = lesson
        self.recommendation = recommendation
        self.confidence = float(confidence)
        self.time = time.time()

    def to_dict(self):
        return {
            "success": self.success,
            "outcome": self.outcome,
            "lesson": self.lesson,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "time": self.time
        }


class ReflectionCore:

    def __init__(self, learning=None):
        self.learning = learning
        self.last_reflection = None
        self.history = []

    def reflect(
        self,
        request,
        action_result=None,
        verification=None
    ):

        request = str(request).strip()

        if verification is None:
            result = ReflectionResult(
                False,
                "UNKNOWN",
                "There was not enough evidence to evaluate the result.",
                "Verify the result before considering the task complete.",
                0.20
            )

        else:

            verified = verification.get(
                "success",
                False
            )

            status = verification.get(
                "status",
                "UNKNOWN"
            )

            if verified:

                result = ReflectionResult(
                    True,
                    "SUCCESS",
                    f"The task '{request}' produced a verified result.",
                    "This approach can be considered reliable for similar tasks.",
                    0.95
                )

            elif status == "UNCERTAIN":

                result = ReflectionResult(
                    False,
                    "UNCERTAIN",
                    f"The task '{request}' produced a result that could not be fully confirmed.",
                    "Perform a stronger verification before reporting success.",
                    0.50
                )

            else:

                result = ReflectionResult(
                    False,
                    "FAILED",
                    f"The task '{request}' did not produce a verified result.",
                    "Do not claim success. Reassess the action and try a safer alternative.",
                    0.90
                )

        self.last_reflection = result

        self.history.append(
            result.to_dict()
        )

        self.history = self.history[-20:]

        if self.learning:
            self.learning.observe(
                f"reflection:{result.outcome}"
            )

        return result

    def status(self):

        return {
            "online": True,
            "history_items": len(self.history),
            "last_outcome": (
                self.last_reflection.outcome
                if self.last_reflection
                else None
            ),
            "last_success": (
                self.last_reflection.success
                if self.last_reflection
                else None
            )
        }
