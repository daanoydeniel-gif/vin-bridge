import re


class ReferenceResolver:
    """Resolve conversational references using recent context and concrete subjects."""

    PRONOUNS = {
        "it", "that", "this", "them", "those",
        "he", "she", "they"
    }

    SOCIAL_PRESENCE_PHRASES = (
        "are you there",
        "are you here",
        "you there",
        "you here",
        "hello vin",
        "hi vin",
        "hey vin",
    )

    FOLLOWUP_STARTS = (
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
        "what do",
    )

    def resolve(self, text, current_topic=None, conversation=None):
        raw = str(text).strip()
        lower = raw.casefold()

        conversation = (
            conversation
            if isinstance(conversation, list)
            else []
        )

        recent_text = self._recent_user_text(conversation)

        tokens = re.findall(
            r"[a-zA-Z0-9']+",
            lower
        )

        references = [
            token
            for token in tokens
            if token in self.PRONOUNS
        ]

        # Short social/presence messages are not follow-ups.
        # This prevents words such as "there" from inheriting
        # an unrelated previous topic such as Downloads or Android.
        is_social_presence = any(
            phrase in lower
            for phrase in self.SOCIAL_PRESENCE_PHRASES
        )

        followup = (
            not is_social_presence
            and len(tokens) <= 10
            and (
                bool(references)
                or lower.startswith(self.FOLLOWUP_STARTS)
            )
        )

        # Prefer a concrete subject from recent conversation.
        subject = self._extract_subject(recent_text)

        # Fall back to the current tracked topic.
        if not subject and followup and current_topic:
            subject = self._normalize_topic(current_topic)

        resolved = raw

        if subject and references:
            resolved = (
                f"{raw} [reference: {subject}]"
            )
        elif subject and followup:
            resolved = (
                f"{raw} [context: {subject}]"
            )

        return {
            "original": raw,
            "resolved": resolved,
            "references": references,
            "followup": followup,
            "subject": subject,
            "recent_text": recent_text,
        }

    def _recent_user_text(self, conversation):
        """Collect recent user messages only."""
        recent = conversation[-5:]

        parts = []

        for item in recent:
            if not isinstance(item, dict):
                continue

            user_text = str(
                item.get("user", "")
            ).strip()

            if user_text:
                parts.append(user_text)

        return " ".join(parts)

    def _extract_subject(self, text):
        """
        Recover useful noun phrases from recent conversation.

        Examples:
            "my school project" -> "school project"
            "the math project" -> "math project"
            "my Vin AI assistant" -> "Vin AI assistant"
        """
        if not text:
            return None

        # Strong, concrete phrases first.
        patterns = (
            r"\bmy\s+([a-zA-Z0-9][a-zA-Z0-9' -]{1,60}?\bproject)\b",
            r"\bthe\s+([a-zA-Z0-9][a-zA-Z0-9' -]{1,60}?\bproject)\b",
            r"\bmy\s+([a-zA-Z0-9][a-zA-Z0-9' -]{1,60}?\bassistant)\b",
            r"\bthe\s+([a-zA-Z0-9][a-zA-Z0-9' -]{1,60}?\bassistant)\b",
        )

        for pattern in patterns:
            matches = re.findall(
                pattern,
                text,
                flags=re.IGNORECASE
            )

            if matches:
                subject = matches[-1]
                return self._clean_subject(subject)

        # Explicit common two-word subject.
        lower = text.casefold()

        if "school project" in lower:
            return "school project"

        if "vin ai assistant" in lower:
            return "Vin AI assistant"

        return None

    def _normalize_topic(self, topic):
        """Turn rough tracker labels into cleaner context."""
        value = str(topic).strip()

        if not value:
            return None

        lower = value.casefold()

        if "school" in lower and "project" in lower:
            return "school project"

        if "vin" in lower and "assistant" in lower:
            return "Vin AI assistant"

        return value

    def _clean_subject(self, subject):
        subject = re.sub(
            r"\s+",
            " ",
            str(subject).strip()
        )

        subject = subject.strip(
            " .,!?;:"
        )

        # Remove accidental conversational tails.
        subject = re.sub(
            r"\s+(is|was|and|but|because|that)$",
            "",
            subject,
            flags=re.IGNORECASE
        )

        return subject
