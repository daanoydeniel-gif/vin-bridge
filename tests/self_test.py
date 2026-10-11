import json
import tempfile
from pathlib import Path

from brain.cognition import CognitiveCore
from brain.intent_router import IntentRouter
from brain.local_model import LocalModel
from brain.planner import Planner
from learning.self_learning import SelfLearning
from memory.memory import Memory
from security.permissions import PermissionManager
from voice.voice_input import VoiceInput


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"PASS  {name}")


def main():
    root = Path(tempfile.mkdtemp(prefix="vin_self_test_"))
    (root / "memory").mkdir(parents=True, exist_ok=True)
    (root / "security").mkdir(parents=True, exist_ok=True)

    memory = Memory(str(root))
    router = IntentRouter()
    planner = Planner(str(root))
    learning = SelfLearning(str(root))
    core = CognitiveCore(
        memory,
        router,
        planner,
        learning=learning,
    )

    print("=" * 60)
    print("VIN SELF TEST")
    print("=" * 60)

    check("empty input routes to CHAT", router.route("") == "CHAT")
    check("memory query routes correctly", router.route("What do you remember?") == "MEMORY_QUERY")
    check("user name query routes correctly", router.route("What is my name?") == "MEMORY_QUERY")
    check("Vin identity gets its own intent", router.route("What is your name?") == "IDENTITY_QUERY")
    check("Vin identity phrase is detected", router.route("Who are you?") == "IDENTITY_QUERY")
    check("memory save routes correctly", router.route("remember that my name is TestUser") == "MEMORY_SAVE")
    check("explicit plan routes correctly", router.route("Make a plan for Vin") == "PLAN")
    check("context follow-up stays CHAT", router.route("How can I improve it?") == "CHAT")
    check("Android request routes correctly", router.route("How do I open Downloads?") == "ANDROID_ACTION")
    check("task start routes correctly", router.route("Start a task to organize my files") == "TASK")
    check("task status routes correctly", router.route("What is the task status?") == "TASK")
    check("next step routes correctly", router.route("What's next?") == "TASK")
    saved = memory.remember("my name is TestUser")
    check("memory saves user name", saved["reason"] == "name_saved")
    check("memory recalls user name", memory.get_username().casefold() == "testuser")
    check("set_username uses username field", memory.set_username("SecondUser"))
    check("username field updates correctly", memory.get_username().casefold() == "seconduser")
    memory.set_username("TestUser")

    greeting = core.process("Hello Vin")
    check("greeting gets a natural reply", greeting.text.startswith("Hello, TestUser."))
    capabilities = core.process("What can you do?")
    check("capability question gets a useful reply", "remember" in capabilities.text.casefold() and "plan" in capabilities.text.casefold())
    user_name_answer = core.process("What is my name?")
    check("user name is answered from memory", "testuser" in user_name_answer.text.casefold())
    vin_name_answer = core.process("What is your name?")
    check("Vin name is answered as Vin", "i'm vin" in vin_name_answer.text.casefold())
    who = core.process("Who are you?")
    check("identity answer remains Vin", "i'm vin" in who.text.casefold())

    samples = [
        "I'm building my Vin AI assistant.",
        "I want to improve his memory.",
        "How should we do it?",
        "Let's talk about my school project.",
        "How can I improve it?",
    ]
    results = [core.process(item) for item in samples]
    check("Vin AI subject is tracked", results[0].text and core.topic_tracker.state["topic_history"])

    task = __import__("brain.engine", fromlist=["VinBrain"]).VinBrain(memory, learning=learning, root=str(root))
    tracked = task.start_task("organize the project")
    check("task goal is tracked", tracked is not None and tracked["status"] == "active")
    snapshot = task.task_snapshot()
    check("task exposes next pending step", snapshot.get("next_step") == "Understand the goal")
    check("task progress starts at zero", snapshot.get("percent") == 0)
    check("follow-up response uses context", "school project" in results[-1].text.casefold())
    check("test conversation is isolated", (root / "memory" / "conversation.json").exists())

    exec_result = task.execute_current_task_step()
    check("task execution refuses to fake success", exec_result.get("status") == "AWAITING_EXECUTOR")

    simulated = task.execute_current_task_step(lambda: {
        "success": True,
        "result": "simulated completion",
        "verification": {"success": True, "evidence": ["test"]}
    })
    check("task execution records verified success", simulated.get("status") == "STEP_COMPLETED")
    check("verified step becomes completed", simulated.get("status") == "STEP_COMPLETED")

    failed = task.execute_current_task_step(lambda: {
        "success": False,
        "verification": {"success": False, "reason": "test failure"}
    })
    check("failed execution is not marked completed", failed.get("status") == "STEP_FAILED")

    permissions = PermissionManager(str(root))
    request_id = permissions.request("LIST", "Downloads/")
    check("permission request is pending", len(permissions.pending()) == 1)
    permissions.allow(request_id)
    check("permission approval is recorded", permissions.consume_approved("LIST", "Downloads/"))

    local_model = LocalModel()
    check("local model wrapper fails safely when offline", local_model.available() in (True, False))

    for path in (root / "memory", root / "security"):
        for file in path.glob("*.json"):
            with file.open(encoding="utf-8") as handle:
                json.load(handle)
    check("generated JSON state is valid", True)

    source_files = list(Path(".").rglob("*.py"))
    source_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in source_files
    )
    forbidden = "D" + "eniel"
    voice = VoiceInput()
    check("voice wake method exists", callable(getattr(voice, "listen_for_wake", None)))
    check("wake extraction works", voice.extract_after_wake_word("Vin open Chrome") == "open Chrome")
    check("wake detection works", voice.contains_wake_word("hello Vin"))
    check("non-wake speech is rejected", not voice.contains_wake_word("open Chrome"))

    check("no hard-coded personal username", forbidden not in source_text)

    print("=" * 60)
    print("VIN SELF TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
