class IntentRouter:
    """Route natural language into deterministic Vin intents."""

    IDENTITY_PHRASES = (
        "what is your name", "what's your name", "who are you",
        "tell me your name", "what should i call you",
    )
    USER_NAME_PHRASES = (
        "what is my name", "what's my name", "who am i",
        "what should you call me", "do you know my name",
    )

    def route(self, text):
        x = str(text).casefold().strip()
        if not x:
            return "CHAT"
        if any(p in x for p in self.IDENTITY_PHRASES):
            return "IDENTITY_QUERY"
        if any(p in x for p in self.USER_NAME_PHRASES):
            return "MEMORY_QUERY"
        if x.startswith(("my name is ", "call me ", "you can call me ")):
            return "MEMORY_SAVE"
        if any(p in x for p in (
            "what do you remember", "do you remember", "what is my ",
            "what's my ", "who is my ", "which is my ",
        )):
            return "MEMORY_QUERY"
        if any(p in x for p in ("remember ", "don't forget", "do not forget", "save this")):
            return "MEMORY_SAVE"
        if any(p in x for p in (
            "start a task", "start task", "begin a task", "begin task",
            "track this task", "track this goal", "work through this task",
            "what is the task status", "what's the task status",
            "what is the progress", "what's the progress",
            "what is next", "what's next", "next step", "continue the task",
        )):
            return "TASK"
        if any(p in x for p in (
            "give you permission", "give vin permission", "give you the authority",
            "give vin the authority", "i'll give you permission",
            "i will give you permission", "i'll give you the authority",
            "i will give you the authority",
        )):
            return "ANDROID_ACTION"
        android_phrases = (
            "phone ui", "phone interface", "access my phone", "access the phone",
            "modify my phone", "modify the phone", "change my phone",
            "attach yourself", "attach vin", "connect yourself to my phone",
            "connect vin to my phone", "control my phone", "operate my phone",
            "open ", "read ", "downloads",
        )
        if any(p in x for p in android_phrases):
            return "ANDROID_ACTION"
        followup_markers = (
            " it", " that", " this", " them", " those", " there",
            " he", " she", " they", " him", " her",
        )
        is_short_followup = len(x.split()) <= 10 and any(m in x for m in followup_markers)
        if not is_short_followup and any(p in x for p in (
            "make a plan", "create a plan", "give me a plan", "plan for ",
            "plan to ", "steps to ", "step-by-step plan", "how do i ", "how can i ",
        )):
            return "PLAN"
        return "CHAT"
