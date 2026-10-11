import json
import os
import time


class GoalState:
    """Persistent lightweight goal state for the active conversation."""

    def __init__(self, root):
        self.file = os.path.join(os.path.abspath(root), "memory", "goal_state.json")
        os.makedirs(os.path.dirname(self.file), exist_ok=True)
        self.state = self._load()

    def _load(self):
        try:
            with open(self.file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else self._default()
        except Exception:
            return self._default()

    def _default(self):
        return {"goal": "", "topic": "", "status": "idle", "confidence": 0.0, "time": 0.0}

    def update(self, goal="", topic="", status="active", confidence=0.0):
        goal = str(goal).strip()
        topic = str(topic).strip()
        if goal:
            self.state["goal"] = goal
        if topic:
            self.state["topic"] = topic
        self.state["status"] = status
        self.state["confidence"] = max(0.0, min(1.0, float(confidence)))
        self.state["time"] = time.time()
        temp = self.file + ".tmp"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
        os.replace(temp, self.file)
        return dict(self.state)

    def current(self):
        return dict(self.state)
