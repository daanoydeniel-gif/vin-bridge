class ContradictionDetector:
    """Detect obvious instruction conflicts without pretending to solve all semantics."""

    def detect(self, text, memories=None, conversation=None):
        lower = str(text).casefold()
        conflicts = []
        if any(x in lower for x in ("don't save", "do not save", "never save")):
            if any(x in lower for x in ("remember", "save this")):
                conflicts.append("The request contains both a prohibition and a save instruction.")
        return {"has_conflict": bool(conflicts), "conflicts": conflicts}
