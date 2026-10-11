import os
import re
import subprocess


class AndroidActions:
    def __init__(self, root):
        self.downloads = os.path.expanduser("~/storage/downloads")

    def list_downloads(self):
        if not os.path.isdir(self.downloads):
            return "Android Downloads is not available."

        try:
            items = sorted(os.listdir(self.downloads))
        except Exception as e:
            return f"Could not read Downloads: {e}"

        return "\n".join(items) if items else "Android Downloads is empty."

    def read_download_file(self, filename):
        safe = os.path.basename(filename)
        path = os.path.join(self.downloads, safe)

        if not os.path.isfile(path):
            return f"File not found in Downloads: {safe}"

        try:
            with open(
                path,
                encoding="utf-8",
                errors="replace"
            ) as f:
                content = f.read()

            return (
                "VIN ACTION RESULT\n"
                "-----------------\n"
                f"File: {safe}\n"
                "Location: Android Downloads\n\n"
                f"CONTENT:\n{content}"
            )

        except Exception as e:
            return f"Could not read file: {e}"

    def open_url(self, url):
        url = url.strip()

        # Only allow normal web URLs.
        if not re.match(r"^https?://", url, re.IGNORECASE):
            return "Invalid URL. Only http:// and https:// URLs are allowed."

        try:
            result = subprocess.run(
                [
                    "am",
                    "start",
                    "-a",
                    "android.intent.action.VIEW",
                    "-d",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode != 0:
                error = result.stderr.strip() or result.stdout.strip()
                return f"Could not open URL: {error}"

            return f"Opened website: {url}"

        except FileNotFoundError:
            return "Android activity command 'am' is unavailable."

        except Exception as e:
            return f"Could not open URL: {e}"
