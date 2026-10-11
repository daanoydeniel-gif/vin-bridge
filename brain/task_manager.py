import json
import os
import time


class TaskManager:

    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.file = os.path.join(
            self.root,
            "memory",
            "tasks.json"
        )

        os.makedirs(
            os.path.dirname(self.file),
            exist_ok=True
        )

        if not os.path.exists(self.file):
            self._save({
                "active_goal": None,
                "tasks": []
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

            data.setdefault("active_goal", None)
            data.setdefault("tasks", [])

            if not isinstance(data["tasks"], list):
                data["tasks"] = []

            return data

        except Exception:
            return {
                "active_goal": None,
                "tasks": []
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

        os.replace(temp, self.file)

    def create_goal(self, goal, steps=None):

        goal = str(goal).strip()

        if not goal:
            return None

        if steps is None:
            steps = []

        data = self._load()

        task = {
            "id": len(data["tasks"]) + 1,
            "goal": goal,
            "steps": [
                {
                    "text": str(step),
                    "status": "pending"
                }
                for step in steps
            ],
            "status": "active",
            "created": time.time(),
            "completed": None
        }

        data["tasks"].append(task)
        data["active_goal"] = task["id"]

        self._save(data)

        return task

    def add_step(self, task_id, step):

        data = self._load()

        for task in data["tasks"]:

            if task["id"] == task_id:

                task["steps"].append({
                    "text": str(step),
                    "status": "pending"
                })

                self._save(data)
                return task

        return None

    def begin_step(self, task_id, step_index):
        """Mark a pending step as executing without claiming success."""
        data = self._load()
        for task in data["tasks"]:
            if task["id"] != task_id:
                continue
            if not (0 <= step_index < len(task["steps"])):
                return None
            step = task["steps"][step_index]
            if step.get("status") != "pending":
                return task
            step["status"] = "executing"
            step["started"] = time.time()
            self._save(data)
            return task
        return None

    def record_step_result(self, task_id, step_index, success, verification=None, result=None):
        """Record an execution result; complete only after verified success."""
        data = self._load()
        for task in data["tasks"]:
            if task["id"] != task_id:
                continue
            if not (0 <= step_index < len(task["steps"])):
                return None
            step = task["steps"][step_index]
            step["result"] = result
            step["verification"] = verification or {}
            step["finished"] = time.time()
            verified = bool(success) and bool((verification or {}).get("success", success))
            step["status"] = "completed" if verified else "failed"
            if verified and task["steps"] and all(x.get("status") == "completed" for x in task["steps"]):
                task["status"] = "completed"
                task["completed"] = time.time()
                if data["active_goal"] == task_id:
                    data["active_goal"] = None
            elif not verified:
                task["status"] = "blocked"
            self._save(data)
            return task
        return None

    def reset_failed_step(self, task_id, step_index):
        """Return a failed step to pending after a correction decision."""
        data = self._load()
        for task in data["tasks"]:
            if task["id"] == task_id and 0 <= step_index < len(task["steps"]):
                task["steps"][step_index]["status"] = "pending"
                task["status"] = "active"
                self._save(data)
                return task
        return None

    def complete_step(self, task_id, step_index):

        data = self._load()

        for task in data["tasks"]:

            if task["id"] != task_id:
                continue

            if not (
                0 <= step_index < len(task["steps"])
            ):
                return None

            task["steps"][step_index]["status"] = "completed"

            if task["steps"] and all(
                step["status"] == "completed"
                for step in task["steps"]
            ):
                task["status"] = "completed"
                task["completed"] = time.time()

                if data["active_goal"] == task_id:
                    data["active_goal"] = None

            self._save(data)

            return task

        return None

    def complete_goal(self, task_id):

        data = self._load()

        for task in data["tasks"]:

            if task["id"] == task_id:

                task["status"] = "completed"
                task["completed"] = time.time()

                for step in task["steps"]:
                    step["status"] = "completed"

                if data["active_goal"] == task_id:
                    data["active_goal"] = None

                self._save(data)

                return task

        return None

    def current(self):

        data = self._load()

        active_id = data.get("active_goal")

        if active_id is None:
            return None

        for task in data["tasks"]:

            if task["id"] == active_id:
                return task

        return None

    def list_tasks(self):

        return self._load()["tasks"]

    def progress(self, task_id=None):

        task = None

        if task_id is None:
            task = self.current()
        else:
            for item in self.list_tasks():
                if item["id"] == task_id:
                    task = item
                    break

        if not task:
            return {
                "found": False,
                "completed": 0,
                "total": 0,
                "percent": 0
            }

        total = len(task["steps"])

        completed = sum(
            1
            for step in task["steps"]
            if step["status"] == "completed"
        )

        percent = (
            round((completed / total) * 100)
            if total
            else 0
        )

        return {
            "found": True,
            "goal": task["goal"],
            "status": task["status"],
            "completed": completed,
            "total": total,
            "percent": percent
        }

    def status(self):

        data = self._load()

        return {
            "online": True,
            "task_count": len(data["tasks"]),
            "active_goal": data["active_goal"]
        }
