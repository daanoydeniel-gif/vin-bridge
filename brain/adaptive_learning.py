import json
import os
import re
import time


class AdaptiveLearning:

    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.file = os.path.join(
            self.root,
            "learning",
            "experience.json"
        )

        os.makedirs(
            os.path.dirname(self.file),
            exist_ok=True
        )

        if not os.path.exists(self.file):
            self._save([])

        self.last_match = None

    def _load(self):
        try:
            with open(
                self.file,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

            return data if isinstance(data, list) else []

        except Exception:
            return []

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

        os.replace(temp, self.file)

    def _words(self, text):
        return set(
            word
            for word in re.findall(
                r"[a-zA-Z0-9_]+",
                str(text).casefold()
            )
            if len(word) >= 3
        )

    def _similarity(self, first, second):

        a = self._words(first)
        b = self._words(second)

        if not a or not b:
            return 0.0

        return len(a & b) / len(a | b)

    def learn(
        self,
        request,
        outcome,
        lesson,
        recommendation="",
        confidence=0.0
    ):

        data = self._load()

        entry = {
            "request": str(request),
            "outcome": str(outcome),
            "lesson": str(lesson),
            "recommendation": str(recommendation),
            "confidence": float(confidence),
            "time": time.time()
        }

        data.append(entry)

        # Keep the experience database bounded.
        data = data[-200:]

        self._save(data)

        return entry

    def recall(self, request, limit=3):

        data = self._load()

        matches = []

        for entry in data:

            score = self._similarity(
                request,
                entry.get("request", "")
            )

            if score <= 0:
                continue

            matches.append(
                (
                    score,
                    entry
                )
            )

        matches.sort(
            key=lambda item: item[0],
            reverse=True
        )

        selected = matches[:limit]

        self.last_match = selected

        return [
            {
                "similarity": round(score, 3),
                "experience": entry
            }
            for score, entry in selected
        ]

    def guidance(self, request):
        """
        Return useful past guidance ranked by both
        similarity and experience confidence.
        """

        matches = self.recall(
            request,
            limit=10
        )

        if not matches:
            return {
                "found": False,
                "guidance": [],
                "matches": []
            }

        ranked = []

        for item in matches:
            experience = item.get(
                "experience",
                {}
            )

            recommendation = str(
                experience.get(
                    "recommendation",
                    ""
                )
            ).strip()

            if not recommendation:
                continue

            try:
                similarity = float(
                    item.get(
                        "similarity",
                        0.0
                    )
                )
            except (TypeError, ValueError):
                similarity = 0.0

            try:
                confidence = float(
                    experience.get(
                        "confidence",
                        0.0
                    )
                )
            except (TypeError, ValueError):
                confidence = 0.0

            similarity = max(
                0.0,
                min(1.0, similarity)
            )

            confidence = max(
                0.0,
                min(1.0, confidence)
            )

            score = similarity * confidence

            ranked.append({
                "score": round(score, 3),
                "similarity": round(
                    similarity,
                    3
                ),
                "confidence": round(
                    confidence,
                    3
                ),
                "recommendation": recommendation,
                "experience": experience
            })

        ranked.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        # Remove duplicate recommendations while
        # preserving the strongest version.
        guidance = []
        seen = set()

        for item in ranked:
            recommendation = item["recommendation"]
            key = recommendation.casefold()

            if key in seen:
                continue

            seen.add(key)
            guidance.append(recommendation)

            # Keep planning guidance concise.
            if len(guidance) >= 3:
                break

        return {
            "found": bool(ranked),
            "guidance": guidance,
            "matches": ranked[:5]
        }

    def status(self):

        data = self._load()

        return {
            "online": True,
            "experience_count": len(data),
            "last_matches": len(
                self.last_match or []
            )
        }
