class DecisionSelector:
    """
    Select the strongest candidate approach using
    similarity, confidence, outcome, and verification.
    """

    def __init__(self):
        self.last_decision = None

    def _clamp(self, value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = 0.0

        return max(0.0, min(1.0, value))

    def score(self, candidate):
        similarity = self._clamp(
            candidate.get("similarity", 0.0)
        )

        confidence = self._clamp(
            candidate.get("confidence", 0.0)
        )

        experience = candidate.get(
            "experience",
            {}
        )

        outcome = str(
            experience.get(
                "outcome",
                "UNKNOWN"
            )
        ).upper()

        verification_bonus = 0.0

        if outcome == "SUCCESS":
            verification_bonus = 0.20

        elif outcome == "UNCERTAIN":
            verification_bonus = -0.20

        elif outcome == "FAILURE":
            verification_bonus = -0.30

        score = (
            similarity * 0.45
            + confidence * 0.35
            + verification_bonus
        )

        return round(
            max(0.0, min(1.0, score)),
            3
        )

    def select(self, candidates):
        if not isinstance(candidates, list):
            return {
                "selected": None,
                "candidates": [],
                "reason": "INVALID_CANDIDATES"
            }

        evaluated = []

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue

            experience = candidate.get(
                "experience",
                {}
            )

            recommendation = str(
                experience.get(
                    "recommendation",
                    ""
                )
            ).strip()

            if not recommendation:
                continue

            evaluated_candidate = dict(candidate)

            evaluated_candidate["decision_score"] = (
                self.score(candidate)
            )

            evaluated.append(
                evaluated_candidate
            )

        evaluated.sort(
            key=lambda item: item["decision_score"],
            reverse=True
        )

        if not evaluated:
            result = {
                "selected": None,
                "candidates": [],
                "reason": "NO_USABLE_CANDIDATES"
            }

            self.last_decision = result
            return result

        selected = evaluated[0]

        experience = selected.get(
            "experience",
            {}
        )

        outcome = str(
            experience.get(
                "outcome",
                "UNKNOWN"
            )
        ).upper()

        if outcome == "SUCCESS":
            reason = "Previously verified successful approach."

        elif outcome == "UNCERTAIN":
            reason = "Best available match, but previous result was uncertain."

        else:
            reason = "Best available learned candidate."

        result = {
            "selected": selected,
            "candidates": evaluated,
            "reason": reason
        }

        self.last_decision = result
        return result

    def status(self):
        return {
            "online": True,
            "has_decision": self.last_decision is not None
        }
