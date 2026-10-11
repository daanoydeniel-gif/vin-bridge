from .context import ContextAnalyzer
from .reference_resolver import ReferenceResolver
from .candidate_generator import CandidateGenerator
from .uncertainty import UncertaintyEvaluator
from .contradiction import ContradictionDetector


class ReasoningEngine:
    """Local multi-stage reasoning: context -> references -> candidates -> scoring."""

    def __init__(self):
        self.context = ContextAnalyzer()
        self.references = ReferenceResolver()
        self.candidates = CandidateGenerator()
        self.uncertainty = UncertaintyEvaluator()
        self.contradictions = ContradictionDetector()
        self.last_result = None

    def reason(self, intent, text, current_topic=None, conversation=None,
               memories=None, experiences=None, goal="", priority="normal"):
        context = self.context.analyze(
            text, current_topic, conversation, memories, experiences
        )
        resolved = self.references.resolve(
            text, current_topic, conversation
        )
        contradiction = self.contradictions.detect(
            text, memories, conversation
        )
        candidates = self.candidates.generate(
            intent, text, resolved, context
        )

        for candidate in candidates:
            score = float(candidate["base_confidence"])
            if resolved.get("subject") and candidate["decision"] == "RESPOND_WITH_CONTEXT":
                score += 0.07
            if context.get("experiences") and candidate["decision"] == "ADAPTIVE_RESPONSE":
                score += 0.05
            if priority == "urgent" and candidate["decision"] == "RESPOND":
                score += 0.02
            if contradiction["has_conflict"]:
                score -= 0.20
            candidate["score"] = max(0.0, min(1.0, score))

        candidates.sort(key=lambda item: item["score"], reverse=True)
        selected = candidates[0]
        uncertainty = self.uncertainty.evaluate(candidates, context)

        result = {
            "decision": selected["decision"],
            "confidence": uncertainty["confidence"],
            "uncertain": uncertainty["uncertain"],
            "margin": uncertainty["margin"],
            "reason": selected["reason"],
            "resolved": resolved,
            "candidates": candidates,
            "contradiction": contradiction,
            "context": context,
            "goal": goal,
        }
        self.last_result = result
        return result

    def status(self):
        return {
            "online": True,
            "has_reasoning": self.last_result is not None,
            "candidate_count": len(self.last_result.get("candidates", [])) if self.last_result else 0,
        }
