import re


class NaturalAndroidActions:

    def __init__(self, controlled):
        self.controlled = controlled

    def handle(self, text):
        lower = text.casefold().strip()

        phrases = [
            "list files in downloads",
            "list downloads",
            "show files in downloads",
            "show downloads",
            "what files are in downloads",
            "what is in downloads",
        ]

        if any(p in lower for p in phrases):
            return self.controlled.list_downloads()

        match = re.search(
            r"(?:read|open)\s+(.+?\.(?:txt|md|log|json))$",
            lower,
        )

        if match:
            return self.controlled.read_file(
                match.group(1).strip()
            )

        # Website opening.
        url_match = re.search(
            r"(?:open|visit|go to)\s+"
            r"(https?://[^\s]+|"
            r"(?:www\.)?[a-z0-9.-]+\.[a-z]{2,}(?:/[^\s]*)?)$",
            lower,
        )

        if url_match:
            value = url_match.group(1).strip()

            if not value.startswith(("http://", "https://")):
                value = "https://" + value

            return self.controlled.open_url(value)

        return None
