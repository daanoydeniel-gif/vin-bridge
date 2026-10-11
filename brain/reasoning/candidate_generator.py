class CandidateGenerator:
    """Generate competing local interpretations instead of making one immediate choice."""

    def generate(self, intent, text, resolved, context):
        candidates = []
        followup = bool(resolved.get("followup"))
        subject = resolved.get("subject")
        experiences = context.get("experiences", [])

        if intent == "PLAN":
            candidates.append(self._candidate("PLAN", "The user wants a structured plan.", 0.92))
        elif intent == "ANDROID_ACTION":
            candidates.append(self._candidate("ACTION", "The request may require an Android action.", 0.91))
        elif intent in ("MEMORY_SAVE", "MEMORY_QUERY"):
            candidates.append(self._candidate("MEMORY", "The request directly concerns stored memory.", 0.96))
        elif intent == "CHAT":
            candidates.append(self._candidate("RESPOND", "Answer conversationally using available context.", 0.72))
            if followup and subject:
                candidates.append(self._candidate(
                    "RESPOND_WITH_CONTEXT",
                    f"Interpret the follow-up as referring to '{subject}'.",
                    0.90
                ))
            # Do not let remembered experiences override ordinary conversation.
            # Adaptive reasoning is used only when the user explicitly asks
            # to reuse previous experience or learned context.
            lower = str(text).casefold()
            adaptive_markers = (
                "based on what we did before",
                "use what you learned",
                "use your previous experience",
                "remember how we did",
                "what did we learn",
            )
            if experiences and any(marker in lower for marker in adaptive_markers):
                candidates.append(self._candidate(
                    "ADAPTIVE_RESPONSE",
                    "Use a relevant previous experience as supporting guidance.",
                    0.78
                ))

        if not candidates:
            candidates.append(self._candidate("RESPOND", "Use a safe direct response.", 0.60))
        return candidates

    def _candidate(self, decision, reason, confidence):
        return {"decision": decision, "reason": reason, "base_confidence": confidence}
