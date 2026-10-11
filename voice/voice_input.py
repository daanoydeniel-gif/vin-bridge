import re
import subprocess


class VoiceInput:
    """Android speech input for Vin."""

    WAKE_WORDS = (
        "vin",
        "finn",
        "ven",
    )

    NO_MATCH = {
        "error_no_match",
        "error: error_no_match",
    }

    def listen(self, timeout=30):
        """Listen for one complete Android speech-recognition session."""
        try:
            result = subprocess.run(
                ["termux-speech-to-text"],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            text = result.stdout.strip()

            if not text:
                return None

            if text.casefold() in self.NO_MATCH:
                return None

            return text

        except subprocess.TimeoutExpired:
            return None

        except Exception as exc:
            return f"[VOICE ERROR] {exc}"

    def listen_for_wake(self, timeout=8):
        """Listen for a short speech-recognition window and return only if Vin is addressed.

        Android's Termux speech recognizer is session-based rather than a true
        always-on hotword engine, so this method keeps the existing recognizer
        and adds the missing wake-word layer without pretending it is real-time.
        """
        text = self.listen(timeout=timeout)
        if not text or text.startswith("[VOICE ERROR]"):
            return None
        if not self.contains_wake_word(text):
            return None
        return text

    def contains_wake_word(self, text):
        if not text:
            return False

        lower = text.casefold()

        return any(
            re.search(
                rf"\b{re.escape(word)}\b",
                lower
            )
            for word in self.WAKE_WORDS
        )

    def extract_after_wake_word(self, text):
        if not text:
            return None

        match = re.search(
            r"\b(?:vin|finn|ven)\b[\s,:-]*(.*)$",
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        remainder = match.group(1).strip()

        return remainder or None


if __name__ == "__main__":
    voice = VoiceInput()

    print("VIN VOICE INPUT")
    print("----------------")
    print("Speak to Vin.")

    while True:
        print("\nListening...")

        text = voice.listen()

        if not text:
            print("No speech recognized.")
            continue

        print("Heard:", text)

        if voice.contains_wake_word(text):
            command = voice.extract_after_wake_word(text)

            if command:
                print("Vin command:", command)
            else:
                print("Vin was called. Waiting for the request...")
        else:
            print("Not directed to Vin.")
