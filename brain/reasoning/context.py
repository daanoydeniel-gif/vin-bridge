class ContextAnalyzer:
    """Build a compact reasoning context from local Vin state."""

    def analyze(self, text, current_topic=None, conversation=None,
                memories=None, experiences=None):
        conversation = conversation if isinstance(conversation, list) else []
        memories = memories if isinstance(memories, list) else []
        experiences = experiences if isinstance(experiences, list) else []
        recent = conversation[-5:]
        return {
            "text": str(text).strip(),
            "current_topic": current_topic,
            "recent_turns": recent,
            "memories": memories[:5],
            "experiences": experiences[:5],
            "has_context": bool(recent or memories or experiences or current_topic),
        }
