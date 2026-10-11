import re
import os

from brain.engine import VinBrain
from brain.local_model import LocalModel
from memory.memory import Memory
from security.permissions import PermissionManager
from tools.controlled_actions import ControlledAndroidActions
from tools.natural_actions import NaturalAndroidActions
from tools.android_bridge import AndroidBridge
from learning.self_model import SelfModel
from learning.self_learning import SelfLearning


ROOT = os.path.dirname(os.path.abspath(__file__))


class Vin:

    def __init__(self):

        self.root = ROOT

        # Core systems
        self.memory = Memory(ROOT)
        self.permission_manager = PermissionManager(ROOT)

        # AI systems
        self.model = LocalModel()
        self.self_model = SelfModel()
        self.learning = SelfLearning(ROOT)

        # Tools
        self.android = ControlledAndroidActions(
            ROOT,
            self.permission_manager
        )

        self.natural_android = NaturalAndroidActions(
            self.android
        )

        self.android_bridge = AndroidBridge(
            ROOT,
            self.android,
            self.permission_manager
        )

        # Cognitive brain
        self.brain = VinBrain(
            self.memory,
            model=self.model,
            learning=self.learning,
            self_model=self.self_model,
            permission_manager=self.permission_manager
        )

    # ---------------------------------
    # IDENTITY
    # ---------------------------------

    def vin_identity(self):
        return "My name is Vin."

    # ---------------------------------
    # BANNER
    # ---------------------------------

    def banner(self):

        print("\n======================================")
        print("            VIN09.3 AI")
        print("======================================")
        print("Cognitive personal assistant")
        print("Memory + Planning + Security + Tools")
        print("Cognitive Core + Response Strategy")
        print("\nType #help for commands.\n")

    # ---------------------------------
    # MEMORY
    # ---------------------------------

    def save_memory(self, text):

        result = self.memory.remember(text)

        if result["reason"] == "name_saved":

            print("\nMEMORY SAVED")
            print("----------------")
            print("Your name:", result["memory"])
            return

        if result["reason"] == "saved":

            print("\nMEMORY SAVED")
            print("----------------")
            print(result["memory"])
            return

        if result["reason"] == "duplicate":

            print("\nMEMORY")
            print("----------------")
            print("I already remember:", result["memory"])
            return

        print("\nMEMORY")
        print("----------------")
        print(result["memory"] or "Nothing to remember.")

    def show_memories(self):

        memories = self.memory.get_memories()

        print("\nVIN MEMORY")
        print("----------------")

        if not memories:
            print("No memories saved.")
            return

        for i, item in enumerate(memories, 1):
            print(f"{i}. {item}")

    def memory_question(self, text):

        lower = text.casefold().strip()

        if "what do you remember" in lower:

            self.show_memories()
            return True

        patterns = [
            r"what is my (.+?)\??$",
            r"what's my (.+?)\??$",
            r"who is my (.+?)\??$",
            r"which is my (.+?)\??$",
            r"do you remember my (.+?)\??$",
        ]

        subject = None

        for pattern in patterns:

            match = re.search(pattern, lower)

            if match:
                subject = match.group(1).strip()
                break

        if not subject:
            return False

        # User identity is stored in Vin's memory; Vin's own identity
        # is handled separately by "#vin" or "what is your name?".
        if subject == "name":
            name = self.memory.get_username()
            print("\nVIN MEMORY")
            print("----------------")
            if name:
                print(f"Your name is {name}.")
            else:
                print("I don't have your name saved yet.")
            return True

        if subject in ("your name", "vin"):
            print("\nVIN")
            print("----------------")
            print(self.vin_identity())
            return True

        results = self.memory.search(
            subject,
            3
        )

        print("\nVIN MEMORY")
        print("----------------")

        if not results:

            print(
                f"I don't remember your {subject} yet."
            )

        else:

            for item in results:
                print("I remember:", item)

        return True

    # ---------------------------------
    # PERMISSIONS
    # ---------------------------------

    def show_permissions(self):

        pending = self.permission_manager.pending()

        print("\nVIN PERMISSIONS")
        print("----------------")

        if not pending:

            print(
                "No pending permission requests."
            )

            return

        for item in pending:

            print(
                f"ID: {item['id']} | "
                f"Action: {item['action']} | "
                f"Target: {item['target']}"
            )

    def permission_action(self, value, allow):

        try:

            rid = int(value.strip())

        except ValueError:

            print("Invalid permission ID.")
            return

        if allow:

            print(
                self.permission_manager.allow(rid)
            )

        else:

            print(
                self.permission_manager.deny(rid)
            )

    # ---------------------------------
    # PLANNING
    # ---------------------------------

    def show_plan(self, goal):

        print("\nVIN PLAN")
        print("----------------")
        print("Goal:", goal)

        for i, step in enumerate(
            self.brain.plan(goal),
            1
        ):

            print(f"{i}. {step}")

    # ---------------------------------
    # TASK LOOP
    # ---------------------------------

    def task_status(self):
        status = self.brain.task_snapshot()
        print("\nVIN TASK STATUS")
        print("----------------")
        if not status.get("found"):
            print("No active task.")
            return
        print("Goal:", status.get("goal"))
        print("Status:", status.get("status"))
        print(
            f"Progress: {status.get('completed', 0)}/"
            f"{status.get('total', 0)} ({status.get('percent', 0)}%)"
        )
        if status.get("next_step"):
            print("Next step:", status["next_step"])

    def start_task(self, goal):
        task = self.brain.start_task(goal)
        if not task:
            print("\nVIN TASK: I need a goal before I can track a task.")
            return
        print("\nVIN TASK STARTED")
        print("----------------")
        print("Goal:", task["goal"])
        for index, step in enumerate(task.get("steps", []), 1):
            print(f"{index}. {step['text']}")

    def next_task_step(self):
        result = self.brain.next_task_step()
        print("\nVIN NEXT STEP")
        print("----------------")
        if not result.get("found"):
            print("No active task.")
            return
        if not result.get("step"):
            print("All steps are complete or the task is ready to be finalized.")
            return
        print(f"Step {result['index'] + 1}: {result['step']['text']}")
        print("Status: pending verification")

    # ---------------------------------
    # SELF INSPECTION
    # ---------------------------------

    def inspect(self):

        print("\nVIN SELF INSPECTION")
        print("----------------")

        for key, value in self.self_model.inspect(
            ROOT
        ).items():

            print(f"{key}: {value}")

    # ---------------------------------
    # STATUS
    # ---------------------------------

    def status(self):

        print("\nVIN09.3 STATUS")
        print("----------------")

        systems = [
            "Core",
            "Intent Router",
            "Cognitive Core",
            "Memory",
            "Security",
            "Planning",
            "Android Tools",
            "Android Bridge",
            "Learning",
            "Response Strategy"
        ]

        for name in systems:

            print(
                f"{name}: ONLINE"
            )

        print(
            "Local AI:",
            "ONLINE"
            if self.model.available()
            else "OFFLINE"
        )

    # ---------------------------------
    # HELP
    # ---------------------------------

    def help(self):

        print("\nVIN09.3 COMMANDS")
        print("----------------")
        print("#status")
        print("#whoami")
        print("#vin")
        print("#memories")
        print("#permissions")
        print("#allow ID")
        print("#deny ID")
        print("#inspect")
        print("#learning")
        print("#plan <goal>")
        print("#task <goal>")
        print("#taskstatus")
        print("#next")
        print("#execute")
        print("#verify")
        print("#android")
        print("#help")
        print("#quit / #exit")

        print(
            "\nNatural requests are also supported."
        )

    # ---------------------------------
    # COMMANDS
    # ---------------------------------

    def command(self, text):

        t = text.strip()
        lower = t.casefold()

        if not t:
            return True

        if lower in (
            "#quit",
            "#exit",
            "exit"
        ):

            print(
                "VIN shutting down."
            )

            return False

        if lower == "#help":

            self.help()
            return True

        if lower == "#status":

            self.status()
            return True

        if lower in (
            "#vin",
            "#identity"
        ):

            print("\nVIN")
            print("----------------")
            print(self.vin_identity())
            return True

        if lower == "#whoami":

            name = self.memory.get_username()

            if name:

                print(
                    f"\nYou are {name}."
                )

            else:

                print(
                    "\nI don't have your name saved yet."
                )

            return True

        if lower == "#memories":

            self.show_memories()
            return True

        if lower == "#permissions":

            self.show_permissions()
            return True

        if lower.startswith("#allow "):

            self.permission_action(
                t[7:],
                True
            )

            return True

        if lower.startswith("#deny "):

            self.permission_action(
                t[6:],
                False
            )

            return True

        if lower == "#inspect":

            self.inspect()
            return True

        if lower == "#learning":

            print("\nVIN LEARNING")
            print("----------------")
            print(
                self.learning.status()
            )

            return True

        if lower.startswith("#task "):
            self.start_task(t[6:].strip())
            return True

        if lower == "#taskstatus":
            self.task_status()
            return True

        if lower == "#next":
            self.next_task_step()
            return True
        if lower == "#execute":
            result = self.brain.execute_current_task_step()
            print("\nVIN TASK EXECUTION")
            print("----------------")
            if result.get("status") == "AWAITING_EXECUTOR":
                print("Step is ready, but no execution bridge is attached yet.")
                print("Vin will not claim that it succeeded.")
            else:
                print("Status:", result.get("status"))
            return True

        if lower == "#verify":
            result = self.brain.verify_current_task_step()
            print("\nVIN TASK VERIFICATION")
            print("----------------")
            if result.get("status") == "AWAITING_VERIFIER":
                print("A verification bridge is required before this step can be completed.")
            else:
                print("Status:", result.get("status"))
            return True


        if lower == "#talk":
            return self.run_voice_conversation()

        if lower == "#voice":
            return self.run_voice_once()

        if lower == "#android":
            status = self.android_bridge.status()
            print("\nVIN ANDROID BRIDGE")
            print("----------------")
            print("Status:", "ONLINE" if status["online"] else "OFFLINE")
            print("Bridge version:", status["version"])
            print("Permission system:", "ONLINE" if status["permission_system"] else "OFFLINE")
            print("Termux Downloads:", "AVAILABLE" if status["termux_downloads"] else "UNAVAILABLE")
            print("Supported actions:", ", ".join(status["supported_actions"]))
            print("Android permissions are never granted automatically.")
            return True


        if lower == "#downloads":
            result = self.android_bridge.list_downloads()

            print("\nVIN ANDROID DOWNLOADS")
            print("---------------------")

            if result.get("status") == "PERMISSION_REQUIRED":
                print(result.get("result", "Permission required."))
            elif result.get("success"):
                print(result.get("result", "No downloads found."))
            else:
                print("Action failed.")
                print(result.get("result", ""))

            return True


        if lower.startswith("#plan "):

            self.show_plan(
                t[6:].strip()
            )

            return True

        return None

    # ---------------------------------
    # COGNITIVE RESPONSE
    # ---------------------------------

    def handle_cognitive_result(
        self,
        text,
        analysis,
        speak=False
    ):

        speaker = None
        if speak:
            from voice.voice_output import VoiceOutput
            speaker = VoiceOutput()

        def output(message):
            message = str(message).strip()
            if not message:
                return
            print("\n" + message)
            if speaker:
                speaker.speak(message)

        intent = analysis["intent"]
        strategy = analysis[
            "response_strategy"
        ]

        # -----------------------------
        # MEMORY QUERY
        # -----------------------------

        if strategy == "answer_from_memory":

            if self.memory_question(text):

                self.learning.observe(
                    "memory query"
                )

                return True

        # -----------------------------
        # MEMORY QUERY WITHOUT RESULT
        # -----------------------------

        if strategy == "ask_clarification":

            if intent == "MEMORY_QUERY":

                if self.memory_question(text):

                    return True

            output("VIN: Could you clarify what you want me to do?")

            return True

        # -----------------------------
        # MEMORY SAVE
        # -----------------------------

        if strategy == "confirm_memory":

            content = text

            lower = text.casefold()

            prefixes = (
                "remember that ",
                "remember my ",
                "remember ",
                "save this ",
                "don't forget ",
                "do not forget "
            )

            for prefix in prefixes:

                if lower.startswith(prefix):

                    content = text[
                        len(prefix):
                    ].strip()

                    break

            self.save_memory(
                content
            )

            self.learning.observe(
                "memory save"
            )

            return True

        # -----------------------------
        # TASK LOOP
        # -----------------------------

        if strategy == "task_response":
            lower = text.casefold().strip()
            if lower in (
                "what is the task status", "what's the task status",
                "what is the progress", "what's the progress",
            ):
                self.task_status()
                return True

            if lower in (
                "what is next", "what's next", "next step",
                "continue the task",
            ):
                self.next_task_step()
                return True

            prefixes = (
                "start a task ", "start task ", "begin a task ",
                "begin task ", "track this task ", "track this goal ",
                "work through this task ",
            )
            goal = text
            for prefix in prefixes:
                if lower.startswith(prefix):
                    goal = text[len(prefix):].strip()
                    break
            self.start_task(goal)
            return True

        # -----------------------------
        # ANDROID ACTION
        # -----------------------------

        if strategy == "perform_action":

            result = self.natural_android.handle(
                text
            )

            if result is not None:

                print("\n" + result)

                self.learning.observe(
                    "android action request"
                )

                return True

        # -----------------------------
        # PLAN
        # -----------------------------

        if strategy == "present_plan":

            self.show_plan(text)

            self.learning.observe(
                "planning request"
            )

            return True

        # -----------------------------
        # NORMAL AI RESPONSE
        # -----------------------------

        # Local AI is optional.
        # Vin must continue working when llama-server is offline.
        response = None

        try:
            if self.model and self.model.available():
                response = self.model.chat(
                    text,
                    system=(
                        "You are Vin, a helpful personal "
                        "Android AI assistant. "
                        "Your identity is Vin. "
                        "Be clear, honest, concise, "
                        "and never claim an action you "
                        "did not perform."
                    )
                )
        except Exception:
            response = None

        self.learning.observe(
            "conversation:" + intent
        )

        if response:
            output(response)
        else:
            # Built-in cognitive fallback.
            try:
                result = self.brain.analyze(text)

                fallback = ""

                if isinstance(result, dict):
                    fallback = str(
                        result.get("text")
                        or result.get("response")
                        or result.get("message")
                        or ""
                    ).strip()

                if fallback:
                    output(fallback)
                else:
                    output(
                        "Vin is ready, but the "
                        "optional local language model "
                        "is currently offline."
                    )

            except Exception as error:
                print(
                    "\nVin cognitive fallback error: "
                    + str(error)
                )

        return True

    # ---------------------------------
    # VOICE MODE
    # ---------------------------------

    def run_voice_conversation(self):
        from voice.voice_input import VoiceInput

        voice = VoiceInput()

        print("\n🎙️ VIN VOICE MODE")
        print("-----------------")
        print("Say 'Vin' when you want to talk to him.")
        print("Say 'goodbye Vin' to end.")

        while True:
            print("\n🎩 Waiting for 'Vin'...")

            wake = voice.listen_for_wake(timeout=8)

            if not wake:
                continue

            print("👂 Vin heard you:", wake)

            wake_lower = wake.casefold().strip()
            if wake_lower in (
                "goodbye vin",
                "goodbye, vin",
                "stop talking vin",
                "stop conversation vin",
            ):
                response = "Goodbye. I'll be here when you need me."
                print("Vin:", response)
                try:
                    from voice.voice_output import VoiceOutput
                    VoiceOutput().speak(response)
                except Exception:
                    pass
                return True

            command = voice.extract_after_wake_word(wake)

            if not command:
                print("🎙️ Listening...")
                command = voice.listen(timeout=15)

            if not command:
                print("I didn't catch that.")
                continue

            print("You >", command)

            lower = command.casefold().strip()

            stop_phrases = (
                "stop talking",
                "stop conversation",
                "end conversation",
                "goodbye vin",
                "goodbye",
                "exit conversation",
            )

            if any(phrase in lower for phrase in stop_phrases):
                response = "Goodbye. I'll be here when you need me."
                print("Vin:", response)

                try:
                    from voice.voice_output import VoiceOutput
                    VoiceOutput().speak(response)
                except Exception:
                    pass

                return True

            approval_phrases = (
                "allow it",
                "approve it",
                "yes allow",
                "yes approve",
                "allow that",
                "approve that",
                "go ahead and allow it",
                "go ahead and approve it",
            )

            if any(phrase in lower for phrase in approval_phrases):
                pending = self.permission_manager.pending()

                if len(pending) == 1:
                    request_id = pending[0]["id"]
                    response = self.permission_manager.allow(request_id)
                    print(response)

                    try:
                        from voice.voice_output import VoiceOutput
                        VoiceOutput().speak("Permission approved.")
                    except Exception:
                        pass

                    continue

                if len(pending) > 1:
                    response = (
                        "I have multiple pending permissions. "
                        "Please specify the permission ID."
                    )
                else:
                    response = "There are no pending permission requests."

                print("Vin:", response)

                try:
                    from voice.voice_output import VoiceOutput
                    VoiceOutput().speak(response)
                except Exception:
                    pass

                continue

            result = self.command(command)

            if result is False:
                return False

            if result is True:
                continue

            analysis = self.brain.analyze(command)

            self.handle_cognitive_result(
                command,
                analysis,
                speak=True
            )

    def run_voice_once(self):

        from voice.voice_input import VoiceInput

        voice = VoiceInput()

        print("\n🎙️ VIN VOICE MODE")
        print("-----------------")
        print("Listening...")

        text = voice.listen()

        if not text:
            print("No speech recognized.")
            return True

        if text.startswith("[VOICE ERROR]"):
            print(text)
            return True

        print("You >", text)

        result = self.command(text)

        if result is False:
            return False

        if result is True:
            return True

        analysis = self.brain.analyze(text)

        self.handle_cognitive_result(
            text,
            analysis,
            speak=True
        )

        return True

    # ---------------------------------
    # MAIN LOOP
    # ---------------------------------

    def run(self):

        self.banner()

        while True:

            try:

                text = input(
                    "You > "
                ).strip()

            except (
                KeyboardInterrupt,
                EOFError
            ):

                print(
                    "\nVIN shutting down."
                )

                break

            result = self.command(
                text
            )

            if result is False:

                break

            if result is True:

                continue

            # ---------------------------------
            # COGNITIVE CORE NOW CONTROLS FLOW
            # ---------------------------------

            analysis = self.brain.analyze(
                text
            )

            self.handle_cognitive_result(
                text,
                analysis
            )


if __name__ == "__main__":
    Vin().run()
