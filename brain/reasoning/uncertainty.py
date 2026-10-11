class UncertaintyEvaluator:
    def evaluate(self, candidates, context):
        if not candidates:
            return {"confidence": 0.0, "uncertain": True, "margin": 0.0}
        scores = sorted(
            (float(c.get("score", 0.0)) for c in candidates),
            reverse=True
        )
        best = scores[0]
        second = scores[1] if len(scores) > 1 else 0.0
        margin = max(0.0, best - second)
        uncertain = best < 0.55 or (len(scores) > 1 and margin < 0.08)
        return {
            "confidence": round(max(0.0, min(1.0, best)), 3),
            "uncertain": uncertain,
            "margin": round(margin, 3),
        }
