import os

from .intent_router import IntentRouter
from .planner import Planner
from .task_manager import TaskManager
from .cognition import CognitiveCore
from .verification import VerificationCore
from .action_loop import ActionLoop
from .reflection import ReflectionCore
from .adaptive_learning import AdaptiveLearning
from .decision_selector import DecisionSelector


class VinBrain:

    def __init__(
        self,
        memory,
        model=None,
        learning=None,
        self_model=None,
        permission_manager=None,
        root=None
    ):
        self.memory = memory
        self.permission_manager = permission_manager

        root = root or os.path.dirname(
            os.path.dirname(__file__)
        )

        self.router = IntentRouter()

        self.task_manager = TaskManager(root)

        self.planner = Planner(
            task_manager=self.task_manager
        )

        self.adaptive_learning = AdaptiveLearning(root)

        self.decision_selector = DecisionSelector()

        self.verification = VerificationCore(root)

        self.action_loop = ActionLoop(
            verification=self.verification,
            learning=learning
        )

        self.reflection = ReflectionCore(
            learning=learning
        )

        self.cognition = CognitiveCore(
            memory=self.memory,
            router=self.router,
            planner=self.planner,
            model=model,
            learning=learning,
            self_model=self_model,
            adaptive_learning=self.adaptive_learning
        )

    # -------------------------
    # COGNITION
    # -------------------------

    def analyze(self, text):

        result = self.cognition.process(text)

        data = result.to_dict()

        data["verification"] = (
            self.verification.status()
        )

        data["action_loop"] = (
            self.action_loop.status()
        )

        data["reflection"] = (
            self.reflection.status()
        )

        data["adaptive_learning"] = (
            self.adaptive_learning.status()
        )

        # Recall relevant past experiences so Vin can use
        # previously learned guidance during future reasoning.
        try:
            learning_guidance = (
                self.adaptive_learning.guidance(text)
            )
        except Exception as error:
            learning_guidance = {
                "found": False,
                "guidance": [],
                "matches": [],
                "error": str(error)
            }

        data["experience_guidance"] = learning_guidance

        data["task_manager"] = (
            self.task_manager.status()
        )

        return data

    # -------------------------
    # PLANNING
    # -------------------------

    def plan(self, goal):
        goal = str(goal).strip()

        if not goal:
            return []

        # Build Vin's normal plan first.
        steps = self.planner.plan(goal)

        # Recall relevant previous experiences.
        try:
            guidance_result = (
                self.adaptive_learning.guidance(goal)
            )
        except Exception:
            guidance_result = {
                "found": False,
                "guidance": [],
                "matches": []
            }

        # Let the Decision Selector choose the strongest
        # learned experience instead of blindly using
        # every recalled recommendation.
        selected_guidance = []

        try:
            decision = self.decision_selector.select(
                guidance_result.get("matches", [])
            )

            selected = decision.get(
                "selected"
            )

            if selected:
                experience = selected.get(
                    "experience",
                    {}
                )

                recommendation = str(
                    experience.get(
                        "recommendation",
                        ""
                    )
                ).strip()

                if recommendation:
                    selected_guidance.append(
                        recommendation
                    )

        except Exception:
            # Keep planning functional even if the selector
            # encounters a problem.
            selected_guidance = []

        # If the selector has no usable decision, fall back
        # to the existing ranked guidance.
        if not selected_guidance:
            selected_guidance = guidance_result.get(
                "guidance",
                []
            )

        # Attach learned guidance without replacing
        # Vin's original planning process.
        if selected_guidance:
            learned_steps = [
                f"Learned guidance: {item}"
                for item in selected_guidance
                if str(item).strip()
            ]

            steps = learned_steps + steps

        return steps

    def create_tracked_goal(self, goal):

        goal = str(goal).strip()

        if not goal:
            return None

        current = self.task_manager.current()

        if current:
            if current.get("goal", "").casefold() == goal.casefold():
                return current

        return self.planner.create_tracked_plan(
            goal
        )

    # -------------------------
    # TASK MANAGEMENT
    # -------------------------

    def current_task(self):
        return self.task_manager.current()

    def task_status(self, task_id=None):
        return self.task_manager.progress(task_id)

    def list_tasks(self):
        return self.task_manager.list_tasks()

    def complete_task_step(
        self,
        task_id,
        step_index
    ):
        return self.planner.complete_step(
            task_id,
            step_index
        )

    def complete_goal(self, task_id):
        return self.planner.complete_goal(
            task_id
        )

    # -------------------------
    # TASK LOOP
    # -------------------------

    def start_task(self, goal):
        """Create or reuse an active tracked task for a user goal."""
        goal = str(goal).strip()
        if not goal:
            return None
        return self.create_tracked_goal(goal)

    def execute_current_task_step(self, executor=None):
        """Run the current step through an injected executor and verify it.

        No executor means the step stays pending; Vin never pretends that an
        unperformed action succeeded.
        """
        task = self.task_manager.current()
        if not task:
            return {"found": False, "status": "NO_TASK"}
        for index, step in enumerate(task.get("steps", [])):
            if step.get("status") in ("pending", "failed"):
                if executor is None:
                    return {"found": True, "index": index, "step": step, "status": "AWAITING_EXECUTOR"}
                self.task_manager.begin_step(task["id"], index)
                try:
                    raw = executor(step["text"], task)
                except Exception as exc:
                    raw = {"success": False, "verification": {"success": False, "reason": str(exc)}}
                if not isinstance(raw, dict):
                    raw = {"success": bool(raw)}
                success = bool(raw.get("success"))
                verification = raw.get("verification") or {"success": success}
                updated = self.task_manager.record_step_result(task["id"], index, success, verification, raw.get("result"))
                return {"found": True, "index": index, "step": updated["steps"][index], "status": updated["steps"][index]["status"], "task": updated}
        return {"found": True, "status": "COMPLETE_OR_BLOCKED", "task": task}

    def verify_current_task_step(self, verifier=None):
        """Verify the current executing step; verification alone can complete it."""
        task = self.task_manager.current()
        if not task:
            return {"found": False, "status": "NO_TASK"}
        for index, step in enumerate(task.get("steps", [])):
            if step.get("status") == "executing":
                if verifier is None:
                    return {"found": True, "status": "AWAITING_VERIFIER", "index": index, "step": step}
                try:
                    raw = verifier(step, task)
                except Exception as exc:
                    raw = {"success": False, "reason": str(exc)}
                if not isinstance(raw, dict):
                    raw = {"success": bool(raw)}
                verification = {"success": bool(raw.get("success")), **raw}
                updated = self.task_manager.record_step_result(task["id"], index, verification["success"], verification, raw.get("result"))
                return {"found": True, "index": index, "step": updated["steps"][index], "status": updated["steps"][index]["status"], "task": updated}
        return {"found": True, "status": "NO_EXECUTING_STEP", "task": task}

    def next_task_step(self):
        """Return the first pending step without executing it."""
        task = self.task_manager.current()
        if not task:
            return {"found": False, "task": None, "step": None}

        for index, step in enumerate(task.get("steps", [])):
            if step.get("status") == "pending":
                return {
                    "found": True,
                    "task": task,
                    "index": index,
                    "step": step,
                }

        return {"found": True, "task": task, "index": None, "step": None}

    def task_snapshot(self):
        """Return progress plus the next pending step for safe reporting."""
        progress = self.task_manager.progress()
        next_step = self.next_task_step()
        progress["next_step"] = (
            next_step.get("step", {}).get("text")
            if next_step.get("step") else None
        )
        progress["next_index"] = next_step.get("index")
        return progress

    # -------------------------
    # ACTION EXECUTION BRIDGE
    # -------------------------

    def reflect(
        self,
        request,
        action_result=None,
        verification=None
    ):
        """
        Bridge VinBrain to the central ReflectionCore.

        ReflectionCore performs the actual reflection and returns
        a ReflectionResult object.
        """

        return self.reflection.reflect(
            request=request,
            action_result=action_result,
            verification=verification
        )

    def execute_action(
        self,
        action,
        description="action",
        learned_guidance=None
    ):
        """
        Execute an action through the central ActionLoop.

        Learned guidance is passed to actions that explicitly
        support the learned_guidance argument.
        """

        if not callable(action):
            return {
                "success": False,
                "status": "INVALID_ACTION",
                "verification": {
                    "success": False,
                    "status": "FAILED",
                    "reason": "Action is not callable.",
                    "evidence": []
                }
            }

        execution_action = action

        if learned_guidance:
            try:
                import inspect

                signature = inspect.signature(action)

                accepts_guidance = (
                    "learned_guidance" in signature.parameters
                    or any(
                        parameter.kind
                        == inspect.Parameter.VAR_KEYWORD
                        for parameter in signature.parameters.values()
                    )
                )

                if accepts_guidance:
                    def guided_action():
                        return action(
                            learned_guidance=learned_guidance
                        )

                    execution_action = guided_action

            except (TypeError, ValueError):
                execution_action = action

        return self.action_loop.execute_and_verify(
            execution_action,
            description
        )

    def run_current_task(
        self,
        action_factory,
        description="task step",
        max_steps=20
    ):
        """
        Execute the active task step-by-step.

        Each step goes through the normal pipeline:
        Decision -> Action -> Verification -> Reflection -> Learning.

        The action_factory receives the current step dictionary
        and returns the callable action for that step.
        """

        task = self.task_manager.current()

        if not task:
            return {
                "success": False,
                "status": "NO_ACTIVE_TASK",
                "steps": [],
                "task": None
            }

        task_id = task["id"]

        results = []

        for _ in range(max_steps):

            current = self.task_manager.current()

            if not current:
                break

            if current.get("status") == "completed":
                return {
                    "success": True,
                    "status": "GOAL_COMPLETE",
                    "steps": results,
                    "task": current
                }

            pending = None

            for step in current.get("steps", []):
                if step.get("status") == "pending":
                    pending = step
                    break

            if pending is None:
                self.task_manager.complete_goal(
                    current["id"]
                )

                return {
                    "success": True,
                    "status": "GOAL_COMPLETE",
                    "steps": results,
                    "task": self.task_manager.current()
                }

            try:
                action = action_factory(pending)

                if not callable(action):
                    return {
                        "success": False,
                        "status": "INVALID_ACTION_FACTORY_RESULT",
                        "steps": results,
                        "task": current
                    }

            except Exception as error:
                return {
                    "success": False,
                    "status": "ACTION_FACTORY_FAILED",
                    "error": str(error),
                    "steps": results,
                    "task": current
                }

            result = self.execute_current_task_step(
                action,
                description or pending.get(
                    "text",
                    "task step"
                )
            )

            results.append(result)

            if not result.get("success", False):
                return {
                    "success": False,
                    "status": "STEP_FAILED",
                    "steps": results,
                    "task": self.task_manager.current()
                }

            # Check immediately after the successful step.
            # This catches completion of the final step.
            updated_task = None

            # The TaskManager clears active_goal when the final
            # step is completed, so current() may return None.
            # Retrieve the completed task by its ID instead.
            for saved_task in self.task_manager.list_tasks():
                if saved_task.get("id") == task_id:
                    updated_task = saved_task
                    break

            if updated_task and updated_task.get("status") == "completed":
                return {
                    "success": True,
                    "status": "GOAL_COMPLETE",
                    "steps": results,
                    "task": updated_task
                }

            # Check immediately after the successful step.
            # This catches completion of the final step.
            updated_task = self.task_manager.current()

            if updated_task and updated_task.get("status") == "completed":
                return {
                    "success": True,
                    "status": "GOAL_COMPLETE",
                    "steps": results,
                    "task": updated_task
                }

        current = self.task_manager.current()

        if current and current.get("status") == "completed":
            return {
                "success": True,
                "status": "GOAL_COMPLETE",
                "steps": results,
                "task": current
            }

        return {
            "success": False,
            "status": "MAX_STEPS_REACHED",
            "steps": results,
            "task": current
        }

    def execute_current_task_step(
        self,
        action=None,
        description="task step"
    ):

        task = self.task_manager.current()

        if not task:
            return {
                "success": False,
                "status": "NO_ACTIVE_TASK",
                "task": None
            }

        pending_index = None

        for index, step in enumerate(
            task.get("steps", [])
        ):
            if step.get("status") == "pending":
                pending_index = index
                break

        if pending_index is None:

            if task.get("status") != "completed":
                self.task_manager.complete_goal(
                    task["id"]
                )

            return {
                "success": True,
                "status": "GOAL_COMPLETE",
                "task": self.task_manager.current()
            }

        step = task["steps"][pending_index]

        if action is None:
            return {
                "success": False,
                "status": "AWAITING_EXECUTOR",
                "step_index": pending_index,
                "step": step["text"],
                "progress": self.task_manager.progress(task["id"]),
                "task": task
            }

        self.task_manager.begin_step(task["id"], pending_index)

        # -------------------------------------------------
        # DECISION
        # -------------------------------------------------

        decision = {
            "selected": None,
            "reason": "NO_LEARNED_DECISION"
        }

        selected_recommendation = None

        try:
            guidance_result = (
                self.adaptive_learning.guidance(
                    step["text"]
                )
            )

            decision = self.decision_selector.select(
                guidance_result.get(
                    "matches",
                    []
                )
            )

            selected = decision.get(
                "selected"
            )

            if selected:
                experience = selected.get(
                    "experience",
                    {}
                )

                selected_recommendation = str(
                    experience.get(
                        "recommendation",
                        ""
                    )
                ).strip() or None

        except Exception as error:
            decision = {
                "selected": None,
                "reason": "DECISION_ERROR",
                "error": str(error)
            }

        # -------------------------------------------------
        # EXECUTION + VERIFICATION
        # -------------------------------------------------

        result = self.execute_action(
            action,
            description or step["text"],
            learned_guidance=selected_recommendation
        )

        verification = result.get(
            "verification",
            {}
        )

        verified = bool(
            verification.get(
                "success",
                False
            )
        )

        # -------------------------------------------------
        # REFLECTION
        # -------------------------------------------------

        reflection = self.reflect(
            request=step["text"],
            action_result=result,
            verification=verification
        )

        reflection_data = reflection.to_dict()

        # -------------------------------------------------
        # LEARNING
        # -------------------------------------------------

        task_result = {
            "step": step["text"],
            "action": result,
            "verification": verification,
            "reflection": reflection_data
        }

        learning_result = self.store_task_lesson(
            task_result
        )

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        if verified:

            updated_task = self.task_manager.record_step_result(
                task["id"],
                pending_index,
                True,
                verification,
                result
            )

            progress = self.task_manager.progress(
                task["id"]
            )

            return {
                "success": True,
                "status": "STEP_COMPLETED",
                "step_index": pending_index,
                "step": step["text"],
                "action": result,
                "decision": {
                    "selected": selected_recommendation,
                    "reason": decision.get(
                        "reason",
                        "UNKNOWN"
                    )
                },
                "verification": verification,
                "reflection": reflection_data,
                "learning": learning_result,
                "progress": progress,
                "task": updated_task
            }

        # -------------------------------------------------
        # FAILURE / UNCERTAIN
        # -------------------------------------------------

        self.task_manager.record_step_result(
            task["id"],
            pending_index,
            False,
            verification,
            result
        )

        return {
            "success": False,
            "status": "STEP_FAILED",
            "step_index": pending_index,
            "step": step["text"],
            "action": result,
            "decision": {
                "selected": selected_recommendation,
                "reason": decision.get(
                    "reason",
                    "UNKNOWN"
                )
            },
            "verification": verification,
            "reflection": reflection_data,
            "learning": learning_result,
            "progress": self.task_manager.progress(
                task["id"]
            ),
            "task": task
        }

    # -------------------------
    # MULTI-STEP GOAL EXECUTION
    # -------------------------

    def permission_status(self):
        if not self.permission_manager:
            return {
                "available": False,
                "reason": "Permission manager is not connected."
            }

        return {
            "available": True,
            "pending": self.permission_manager.pending()
        }

    def request_task_permission(self, action, target):
        if not self.permission_manager:
            return {
                "success": False,
                "status": "PERMISSION_SYSTEM_UNAVAILABLE"
            }

        request_id = self.permission_manager.request(
            action,
            target
        )

        return {
            "success": False,
            "status": "PERMISSION_REQUIRED",
            "id": request_id,
            "action": action,
            "target": target
        }

    def approve_permission(self, request_id):
        if not self.permission_manager:
            return "Permission system unavailable."

        return self.permission_manager.allow(
            request_id
        )

    def deny_permission(self, request_id):
        if not self.permission_manager:
            return "Permission system unavailable."

        return self.permission_manager.deny(
            request_id
        )

    def execute_task_step_with_permission(
        self,
        action,
        action_name,
        target,
        description="task step",
        require_permission=True
    ):
        if require_permission:
            if not self.permission_manager:
                return {
                    "success": False,
                    "status": "PERMISSION_SYSTEM_UNAVAILABLE"
                }

            approved = (
                self.permission_manager
                .consume_approved(
                    action_name,
                    target
                )
            )

            if not approved:
                return self.request_task_permission(
                    action_name,
                    target
                )

        return self.execute_current_task_step(
            action,
            description
        )

    def store_task_lesson(self, task_result):
        """
        Store a lesson while respecting verification confidence.
        Uncertain results may be remembered, but they are never treated
        as strongly reliable experiences.
        """

        if not isinstance(task_result, dict):
            return {
                "success": False,
                "status": "INVALID_TASK_RESULT"
            }

        reflection = task_result.get("reflection", {})

        if not isinstance(reflection, dict):
            return {
                "success": False,
                "status": "NO_REFLECTION"
            }

        verification = task_result.get(
            "verification",
            {}
        )

        if not isinstance(verification, dict):
            verification = {}

        verification_success = verification.get(
            "success",
            False
        )

        verification_status = str(
            verification.get(
                "status",
                "UNKNOWN"
            )
        ).upper()

        lesson = str(
            reflection.get("lesson", "")
        ).strip()

        if not lesson:
            return {
                "success": False,
                "status": "NO_LESSON"
            }

        learning = getattr(
            self,
            "learning",
            None
        )

        if learning is None:
            learning = getattr(
                self,
                "adaptive_learning",
                None
            )

        if learning is None:
            return {
                "success": False,
                "status": "LEARNING_SYSTEM_UNAVAILABLE"
            }

        try:
            original_confidence = float(
                reflection.get(
                    "confidence",
                    0.0
                )
            )

            original_confidence = max(
                0.0,
                min(1.0, original_confidence)
            )

            if verification_success:
                learning_outcome = str(
                    reflection.get(
                        "outcome",
                        "SUCCESS"
                    )
                )

                confidence = original_confidence
                learning_status = "RELIABLE_LESSON"

            elif verification_status == "UNCERTAIN":
                learning_outcome = "UNCERTAIN"

                # Remember the experience cautiously.
                # Never allow an uncertain result to become
                # a high-confidence reliable lesson.
                confidence = min(
                    original_confidence,
                    0.25
                )

                learning_status = "CAUTIOUS_LESSON"

            else:
                learning_outcome = str(
                    reflection.get(
                        "outcome",
                        "FAILURE"
                    )
                )

                confidence = min(
                    original_confidence,
                    0.40
                )

                learning_status = "FAILURE_LESSON"

            entry = learning.learn(
                request=task_result.get(
                    "step",
                    "task step"
                ),
                outcome=learning_outcome,
                lesson=lesson,
                recommendation=reflection.get(
                    "recommendation",
                    ""
                ),
                confidence=confidence
            )

            return {
                "success": True,
                "status": "LESSON_STORED",
                "learning_status": learning_status,
                "lesson": lesson,
                "verification_status": verification_status,
                "confidence": confidence,
                "experience": entry
            }

        except Exception as error:
            return {
                "success": False,
                "status": "LEARNING_ERROR",
                "error": str(error)
            }

