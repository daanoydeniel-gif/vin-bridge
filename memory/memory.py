import json
import os
import re


class Memory:

    def __init__(self, root):
        self.root = os.path.abspath(root)

        self.file = os.path.join(
            self.root,
            "memory",
            "memory.json"
        )

        os.makedirs(
            os.path.dirname(self.file),
            exist_ok=True
        )

        if not os.path.exists(self.file):
            self._save({
                "username": None,
                "memories": []
            })

    def _load(self):
        try:
            with open(
                self.file,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

            if not isinstance(data, dict):
                data = {}

            data.setdefault("username", data.get("name"))
            data.pop("name", None)
            data.setdefault("memories", [])

            if not isinstance(data["memories"], list):
                data["memories"] = []

            return data

        except Exception:
            return {
                "username": None,
                "memories": []
            }

    def _save(self, data):
        temp = self.file + ".tmp"

        with open(
            temp,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False
            )

        os.replace(
            temp,
            self.file
        )

    def _memory_text(self, item):
        if isinstance(item, str):
            return item

        if isinstance(item, dict):
            for key in (
                "text",
                "memory",
                "content",
                "value"
            ):
                value = item.get(key)

                if isinstance(value, str):
                    return value

        return str(item)

    def _extract_name(self, text):
        text = str(text).strip()

        patterns = [
            r"^(?:remember\s+)?that\s+my\s+name\s+is\s+(.+?)$",
            r"^(?:remember\s+)?my\s+name\s+is\s+(.+?)$",
            r"^my\s+name\s+is\s+(.+?)$",
            r"^(?:remember\s+)?name\s+is\s+(.+?)$",
            r"^name\s+is\s+(.+?)$",
            r"^(?:remember\s+)?my\s+name\s+(.+?)$",
        ]

        for pattern in patterns:
            match = re.match(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:
                name = match.group(1).strip()

                name = re.sub(
                    r"[.!?,]+$",
                    "",
                    name
                ).strip()

                if name:
                    return name

        return None

    def _recover_name(self, data):
        name = data.get("username")

        if isinstance(name, str) and name.strip():
            return name.strip()

        for item in reversed(data["memories"]):
            memory_text = self._memory_text(item)
            recovered = self._extract_name(memory_text)

            if recovered:
                data["username"] = recovered
                self._save(data)
                return recovered

        return None

    def remember(self, text):
        data = self._load()

        text = str(text).strip()

        if not text:
            return {
                "saved": False,
                "reason": "empty",
                "memory": ""
            }

        name = self._extract_name(text)

        if name:
            data["username"] = name

            cleaned = []

            for item in data["memories"]:
                memory_text = self._memory_text(item)

                if self._extract_name(memory_text):
                    continue

                cleaned.append(item)

            data["memories"] = cleaned

            self._save(data)

            return {
                "saved": True,
                "reason": "name_saved",
                "memory": name
            }

        text_lower = text.casefold()

        for item in data["memories"]:
            memory_text = self._memory_text(item)

            if memory_text.casefold() == text_lower:
                return {
                    "saved": False,
                    "reason": "duplicate",
                    "memory": memory_text
                }

        data["memories"].append(text)
        data["memories"] = data["memories"][-100:]

        self._save(data)

        return {
            "saved": True,
            "reason": "saved",
            "memory": text
        }

    def get_username(self):
        data = self._load()
        return self._recover_name(data)

    def set_username(self, username):
        username = str(username).strip()

        if not username:
            return False

        data = self._load()
        data["username"] = username

        cleaned = []

        for item in data["memories"]:
            memory_text = self._memory_text(item)

            if self._extract_name(memory_text):
                continue

            cleaned.append(item)

        data["memories"] = cleaned

        self._save(data)

        return True

    # Backward-compatible aliases used by the existing cognitive layer.
    def get_name(self):
        return self.get_username()

    def set_name(self, name):
        return self.set_username(name)

    def get_memories(self):
        data = self._load()

        memories = []

        name = self._recover_name(data)

        if name:
            memories.append(
                f"My name is {name}"
            )

        for item in data["memories"]:
            text = self._memory_text(item)

            if text and text not in memories:
                memories.append(text)

        return memories

    def search(self, query, limit=5):
        data = self._load()

        query = str(query).casefold().strip()

        if not query:
            return []

        results = []

        name = self._recover_name(data)

        if name:
            if (
                query in "name"
                or query in name.casefold()
                or "name" in query
            ):
                results.append(
                    f"My name is {name}"
                )

        for item in reversed(data["memories"]):
            memory_text = self._memory_text(item)

            if query in memory_text.casefold():
                if memory_text not in results:
                    results.append(memory_text)

            if len(results) >= limit:
                break

        return results[:limit]
