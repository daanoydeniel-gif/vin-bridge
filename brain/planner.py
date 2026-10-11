class Planner:

    def __init__(self, task_manager=None):
        self.task_manager = task_manager

    def plan(self, goal):

        goal = str(goal).strip()

        if not goal:
            return ["Clarify the goal."]

        return [
            "Understand the goal",
            "Break it into smaller tasks",
            "Check tools and permissions",
            "Perform safe actions with approval",
            "Verify the result",
            "Reflect on the result",
            "Store the useful lesson",
            "Report the result"
        ]

    def create_tracked_plan(self, goal):

        if not self.task_manager:
            return None

        steps = self.plan(goal)

        task = self.task_manager.create_goal(
            goal,
            steps
        )

        return task

    def current_progress(self):

        if not self.task_manager:
            return {
                "found": False,
                "completed": 0,
                "total": 0,
                "percent": 0
            }

        return self.task_manager.progress()

    def complete_step(
        self,
        task_id,
        step_index
    ):

        if not self.task_manager:
            return None

        return self.task_manager.complete_step(
            task_id,
            step_index
        )

    def complete_goal(self, task_id):

        if not self.task_manager:
            return None

        return self.task_manager.complete_goal(
            task_id
        )
