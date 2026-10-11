import json
import os
import re
import time


class TopicTracker:
    """
    Tracks the current conversation topic using lightweight
    local heuristics. No external API is required.
    """

    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.file = os.path.join(
            self.root,
            "memory",
            "topic.json"
        )

        os.makedirs(os.path.dirname(self.file), exist_ok=True)

        self.state = self._load()

    def _load(self):
        try:
            with open(self.file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                return data
        except Exception:
            pass

        return {
            "current_topic": None,
            "previous_topic": None,
            "topic_history": []
        }

    def _save(self):
        temp = self.file + ".tmp"

        with open(temp, "w", encoding="utf-8") as f:
            json.dump(
                self.state,
                f,
                indent=2,
                ensure_ascii=False
            )

        os.replace(temp, self.file)

    def _clean(self, text):
        return re.sub(
            r"[^a-zA-Z0-9\s]",
            " ",
            str(text).casefold()
        )

    def _keywords(self, text):
        words = self._clean(text).split()

        ignored = {
            "the", "and", "for", "with", "this",
            "that", "what", "how", "why", "can",
            "you", "your", "about", "want", "need",
            "please", "help", "tell", "does", "is",
            "are", "was", "were", "his", "her"
        }

        return {
            word
            for word in words
            if len(word) >= 3 and word not in ignored
        }

    def similarity(self, first, second):
        a = self._keywords(first)
        b = self._keywords(second)

        if not a or not b:
            return 0.0

        return len(a & b) / len(a | b)

    def detect(self, text, previous_text=""):
        current_words = self._keywords(text)
        previous_words = self._keywords(previous_text)

        reset_words = {
            "different",
            "another",
            "unrelated",
            "change",
            "topic"
        }

        if current_words & reset_words:
            return "general"

        current_topic = self.state.get(
            "current_topic"
        )

        # Detect short conversational follow-ups.
        raw_words = set(
            self._clean(text).split()
        )

        followup_words = {
            "it",
            "that",
            "this",
            "them",
            "those",
            "there"
        }

        followup_starts = (
            "how should",
            "how can",
            "how do",
            "what should",
            "what about",
            "can we",
            "could we",
            "should we",
            "why does",
            "why is",
            "what is",
            "what do"
        )

        cleaned = self._clean(text).strip()

        is_followup = (
            len(raw_words) <= 8
            and (
                bool(raw_words & followup_words)
                or any(
                    cleaned.startswith(start)
                    for start in followup_starts
                )
            )
        )

        if is_followup and current_topic:
            return current_topic

        if previous_text and self.similarity(
            text,
            previous_text
        ) >= 0.25:
            return current_topic or self._make_topic(text)

        return self._make_topic(text)

    def _make_topic(self, text):
        cleaned = self._clean(text)

        # Preserve concrete project/assistant subjects instead of
        # reducing them to a generic keyword ordering.
        if "school project" in cleaned:
            return "school project"

        if "vin ai assistant" in cleaned:
            return "Vin AI assistant"

        words = sorted(
            self._keywords(text),
            key=lambda x: (-len(x), x)
        )

        if not words:
            return "general"

        return " ".join(words[:3])

    def update(self, text, previous_text=""):
        new_topic = self.detect(
            text,
            previous_text
        )

        old_topic = self.state.get(
            "current_topic"
        )

        if old_topic != new_topic:
            self.state["previous_topic"] = old_topic

        self.state["current_topic"] = new_topic

        history = self.state.setdefault(
            "topic_history",
            []
        )

        history.append({
            "topic": new_topic,
            "time": time.time()
        })

        self.state["topic_history"] = history[-30:]

        self._save()

        return new_topic

    def current(self):
        return self.state.get(
            "current_topic"
        )

    def previous(self):
        return self.state.get(
            "previous_topic"
        )

    def status(self):
        return {
            "online": True,
            "current_topic": self.current(),
            "previous_topic": self.previous(),
            "history_items": len(
                self.state.get("topic_history", [])
            )
        }
