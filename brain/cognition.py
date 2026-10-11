import time
import json
import os
from .topic_tracker import TopicTracker
from .reasoning.reasoning_engine import ReasoningEngine


class CognitiveResult:

    def __init__(
        self,
        text,
        intent,
        memories=None,
        experiences=None,
        decision="RESPOND",
        plan=None,
        confidence=0.0,
        reason="",
        goal="",
        mode="conversation",
        priority="normal",
        response_strategy="answer"
    ):
        self.text = text
        self.intent = intent
        self.memories = memories or []
        self.experiences = experiences or []
        self.decision = decision
        self.plan = plan or []
        self.confidence = confidence
        self.reason = reason
        self.goal = goal
        self.mode = mode
        self.priority = priority
        self.response_strategy = response_strategy
        self.reasoning = {}
        self.time = time.time()

    def to_dict(self):
        return {
            "text": self.text,
            "intent": self.intent,
            "memories": self.memories,
            "experiences": self.experiences,
            "decision": self.decision,
            "plan": self.plan,
            "confidence": self.confidence,
            "reason": self.reason,
            "goal": self.goal,
            "mode": self.mode,
            "priority": self.priority,
            "response_strategy": self.response_strategy,
            "reasoning": self.reasoning,
            "time": self.time
        }


class CognitiveCore:

    def __init__(
        self,
        memory,
        router,
        planner,
        model=None,
        learning=None,
        self_model=None,
        adaptive_learning=None
    ):
        self.memory = memory
        self.router = router
        self.planner = planner
        self.model = model
        self.learning = learning
        self.self_model = self_model
        self.adaptive_learning = adaptive_learning

        self.last_result = None

        # Keep all cognitive state inside the same project root as Memory.
        # This also makes isolated development tests safe and reproducible.
        self.root = getattr(
            memory,
            "root",
            os.path.dirname(os.path.dirname(__file__))
        )
        self.root = os.path.abspath(self.root)

        self.conversation_file = os.path.join(
            self.root,
            "memory",
            "conversation.json"
        )

        os.makedirs(
            os.path.dirname(self.conversation_file),
            exist_ok=True
        )

        self.conversation = self._load_conversation()

        self.topic_tracker = TopicTracker(self.root)
        self.reasoning_engine = ReasoningEngine()
        self.goal_state = __import__(
            "brain.reasoning.goal_state",
            fromlist=["GoalState"]
        ).GoalState(self.root)


    def understand(self, text):

        text = str(text).strip()

        if not text:
            return {
                "text": "",
                "intent": "EMPTY"
            }

        return {
            "text": text,
            "intent": self.router.route(text)
        }

    def extract_goal(self, text, intent):

        lower = text.casefold().strip()

        if intent == "MEMORY_SAVE":

            prefixes = (
                "remember that ",
                "remember ",
                "don't forget ",
                "do not forget ",
                "save this "
            )

            for prefix in prefixes:

                if lower.startswith(prefix):
                    return text[len(prefix):].strip()

        if intent in (
            "PLAN",
            "ANDROID_ACTION",
            "MEMORY_QUERY",
            "IDENTITY_QUERY"
        ):
            return text

        return ""

    def detect_priority(self, text):

        x = text.casefold()

        if any(
            word in x
            for word in (
                "urgent",
                "emergency",
                "asap",
                "immediately",
                "right now"
            )
        ):
            return "urgent"

        if any(
            word in x
            for word in (
                "important",
                "quickly",
                "need this"
            )
        ):
            return "high"

        return "normal"

    def determine_mode(self, intent):

        modes = {
            "MEMORY_SAVE": "memory",
            "MEMORY_QUERY": "memory",
            "IDENTITY_QUERY": "conversation",
            "TASK": "task",
            "ANDROID_ACTION": "action",
            "PLAN": "planning",
            "CHAT": "conversation",
            "EMPTY": "idle"
        }

        return modes.get(
            intent,
            "conversation"
        )

    def _load_conversation(self):
        try:
            with open(
                self.conversation_file,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

            if isinstance(data, list):
                return data[-50:]

        except Exception:
            pass

        return []

    def _save_conversation(self):
        try:
            temp = self.conversation_file + ".tmp"

            with open(
                temp,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    self.conversation[-50:],
                    f,
                    indent=2,
                    ensure_ascii=False
                )

            os.replace(
                temp,
                self.conversation_file
            )

        except Exception:
            pass

    def gather_conversation_context(self, limit=5):
        if not self.conversation:
            return []

        return self.conversation[-limit:]

    def gather_context(self, text):

        words = [
            word.strip(
                ".,!?;:\"'()[]{}"
            )
            for word in text.casefold().split()
        ]

        memories = []

        for word in words:

            if len(word) < 4:
                continue

            results = self.memory.search(
                word,
                3
            )

            for result in results:

                if result not in memories:
                    memories.append(result)

            if len(memories) >= 5:
                break

        return memories[:5]

    def gather_experience(self, text):

        if not self.adaptive_learning:
            return []

        try:
            matches = self.adaptive_learning.recall(
                text,
                limit=3
            )

            return matches

        except Exception:
            return []

    def reason(
        self,
        understood,
        memories,
        experiences,
        goal,
        mode,
        priority,
        conversation_context=None,
        current_topic=None
    ):

        intent = understood["intent"]

        advanced = self.reasoning_engine.reason(
            intent=intent,
            text=understood["text"],
            current_topic=current_topic,
            conversation=conversation_context,
            memories=memories,
            experiences=experiences,
            goal=goal,
            priority=priority
        )

        if advanced["uncertain"] and intent == "CHAT":
            return {
                "decision": "RESPOND",
                "confidence": advanced["confidence"],
                "reason": (
                    "Multiple interpretations were considered, but confidence is limited. "
                    + advanced["reason"]
                ),
                "advanced": advanced
            }

        return {
            "decision": advanced["decision"],
            "confidence": advanced["confidence"],
            "reason": advanced["reason"],
            "advanced": advanced
        }


    def choose_response_strategy(
        self,
        intent,
        decision,
        memories,
        experiences,
        priority
    ):

        if intent == "EMPTY":
            return "ask_clarification"

        if intent == "MEMORY_QUERY":
            return "answer_from_memory"

        if intent == "IDENTITY_QUERY":
            return "direct_response"

        if intent == "TASK":
            return "task_response"

        if intent == "MEMORY_SAVE":
            return "confirm_memory"

        if intent == "ANDROID_ACTION":
            return "perform_action"

        if intent == "PLAN":
            return "present_plan"

        # Ordinary conversation should remain conversational. Learned
        # experiences are supporting context, not permission to replace
        # the user's direct request with a generic learning message.
        if priority == "urgent":
            return "direct_response"

        if intent == "CHAT":
            return "conversational_response"

        return "direct_response"

    def make_plan(self, text, decision):

        if decision != "PLAN":
            return []

        return self.planner.plan(text)

    def _build_response(
        self,
        text,
        intent,
        reasoning,
        strategy,
        goal,
        current_topic
    ):
        """
        Local natural-response layer.

        Uses Vin's reasoning state, topic, goal,
        context, and conversation history without
        requiring an external language model.
        """

        advanced = (
            reasoning.get("advanced", {})
            if isinstance(reasoning, dict)
            else {}
        )

        decision = str(
            advanced.get("decision")
            or reasoning.get("decision", "RESPOND")
        )

        resolved = advanced.get("resolved", {})
        context = advanced.get("context", {})

        subject = ""
        if isinstance(resolved, dict):
            subject = str(
                resolved.get("subject") or ""
            ).strip()

        subject = (
            subject
            or str(current_topic or "").strip()
            or str(goal or "").strip()
        )

        lower = str(text).casefold().strip()

        # ---------------------------------
        # NATURAL SOCIAL CHAT
        # ---------------------------------
        # Greetings and simple social messages should not be
        # turned into a topic/status report. Vin should sound
        # like a conversational assistant first, while the
        # deeper reasoning system remains available underneath.
        greetings = (
            "hello", "hi", "hey", "good morning",
            "good afternoon", "good evening", "good night"
        )

        if intent == "CHAT":
            if lower in greetings or lower.startswith("hello vin") or lower.startswith("hi vin") or lower.startswith("hey vin"):
                username = self.memory.get_username() if self.memory else None
                if username:
                    return f"Hello, {username}. I'm here. What would you like to do?"
                return "Hello. I'm here. What would you like to do?"

            if lower in (
                "how are you", "how are you vin",
                "how are you doing"
            ):
                return "I'm doing well and ready to help. What are we working on?"

            if lower in (
                "what is your name", "what is your name?",
                "what's your name", "what's your name?",
                "who are you", "who are you?"
            ):
                return "I'm Vin, your personal AI assistant. I'm here and ready to help."

            if lower in (
                "what can you do", "what can you do?",
                "what do you do", "what are you capable of"
            ):
                return (
                    "I can keep track of our conversation, remember useful information, "
                    "reason through problems, make plans, learn from completed tasks, "
                    "and handle approved phone actions. What would you like to try?"
                )

            if lower in ("thanks", "thank you", "thanks vin", "thank you vin"):
                return "You're welcome. I'm ready for the next thing whenever you are."

            if lower in ("okay", "ok", "alright", "got it"):
                return "Got it. I'm following you."

        # ---------------------------------
        # VIN IDENTITY
        # ---------------------------------

        if intent == "IDENTITY_QUERY":
            return "I'm Vin, your personal AI assistant. My identity is separate from the person using me."

        # ---------------------------------
        # MEMORY
        # ---------------------------------

        if intent == "MEMORY_SAVE":
            return (
                "Understood. I'll save that as a "
                "memory and use it when it becomes "
                "relevant."
            )

        if intent == "MEMORY_QUERY":
            # User identity is a live memory field, not a scripted identity.
            # Keep this separate from Vin's own identity.
            if lower in (
                "what is my name", "what is my name?",
                "what's my name", "what's my name?",
            ):
                username = self.memory.get_username() if self.memory else None
                if username:
                    return f"Your name is {username}."
                return "I don't have your name saved yet."

            if self.memory:
                return (
                    "I'll check my stored memories "
                    "and use the relevant information."
                )

            return (
                "I don't have a stored memory that "
                "I can use for that yet."
            )

        # ---------------------------------
        # TASK LOOP
        # ---------------------------------

        if intent == "TASK":
            if lower in (
                "what is the task status", "what's the task status",
                "what is the progress", "what's the progress",
                "what is next", "what's next", "next step",
                "continue the task",
            ):
                return (
                    "I’ll check the active task, report its verified progress, "
                    "and identify the next pending step without claiming it is complete."
                )

            return (
                "I can track that as an active task: define the goal, work through "
                "each step, verify each result, and only mark a step complete when "
                "there is evidence it succeeded."
            )

        # ---------------------------------
        # PLANNING
        # ---------------------------------

        if intent == "PLAN":
            steps = self.planner.plan(text)

            if steps:
                first_steps = steps[:3]
                formatted = "; ".join(
                    str(step) for step in first_steps
                )

                return (
                    "I would approach it in stages: "
                    + formatted
                    + "."
                )

            return (
                "I'll break the goal into smaller "
                "steps and work through them carefully."
            )

        # ---------------------------------
        # ANDROID ACTION
        # ---------------------------------

        if intent == "ANDROID_ACTION":
            lower_action = lower
            if any(phrase in lower_action for phrase in (
                "phone ui", "phone interface", "access the phone",
                "access my phone", "modify my phone", "modify the phone",
                "attach yourself", "attach vin", "connect yourself to my phone",
                "connect vin to my phone", "control my phone", "operate my phone",
            )):
                return (
                    "I can help connect Vin to the Android side of your phone. "
                    "We'll add the phone bridge, request only the permissions "
                    "we need, and verify each action instead of claiming control "
                    "I haven't actually been given."
                )
            if any(phrase in lower_action for phrase in (
                "permission", "authority", "allow", "authorize",
            )):
                return (
                    "Thank you. I can use that permission when the Android bridge "
                    "is connected. I'll still request and verify each specific "
                    "phone capability instead of assuming unlimited access."
                )
            return (
                "I understand the requested phone action. Before performing it, "
                "I'll check the required permission and verify the result."
            )

        # ---------------------------------
        # FOLLOW-UP WITH CONTEXT
        # ---------------------------------

        if decision == "RESPOND_WITH_CONTEXT":
            if subject:
                if lower.startswith("how"):
                    return (
                        f"Since we're working on "
                        f"{subject}, I'd start by "
                        "identifying what we already "
                        "have, then improve one part "
                        "at a time and test each change."
                    )

                if lower.startswith("why"):
                    return (
                        f"That question relates to "
                        f"{subject}. I'll use the "
                        "conversation context before "
                        "forming the answer."
                    )

                return (
                    f"I'll keep {subject} as the "
                    "current context and build the "
                    "answer around it."
                )

            return (
                "I'm following the current conversation "
                "context and will use it for the answer."
            )

        # ---------------------------------
        # LEARNED EXPERIENCE
        # ---------------------------------

        if decision == "ADAPTIVE_RESPONSE":
            experiences = context.get(
                "experiences", []
            )

            if experiences:
                return (
                    "I found a relevant previous "
                    "experience. I'll use it as guidance, "
                    "then verify that it still fits "
                    "the current situation."
                )

            return (
                "I can use previous experience as "
                "guidance, but I'll verify it first."
            )

        # ---------------------------------
        # NORMAL CHAT
        # ---------------------------------

        if intent == "CHAT":
            if subject and subject.casefold() not in {
                "hello vin", "hello", "hi", "hey", "general"
            }:
                return (
                    f"I’m with you. We’re working on {subject}. "
                    "Tell me what you want to change, understand, or do next."
                )

            if self.conversation:
                return (
                    "I’m following the conversation. Tell me what you want "
                    "to work on next."
                )

            return "I’m here and listening. What would you like to do?"

        # ---------------------------------
        # SAFE DEFAULT
        # ---------------------------------

        return (
            "I understand your request. I'll "
            "reason through it carefully before "
            "deciding what to do."
        )

    def process(self, text):

        start = time.time()

        understood = self.understand(text)

        intent = understood["intent"]

        goal = self.extract_goal(
            understood["text"],
            intent
        )

        mode = self.determine_mode(
            intent
        )

        priority = self.detect_priority(
            understood["text"]
        )

        memories = self.gather_context(
            understood["text"]
        )

        experiences = self.gather_experience(
            understood["text"]
        )

        previous_message = ""

        if self.conversation:
            previous_message = str(
                self.conversation[-1].get("user", "")
            )

        current_topic = self.topic_tracker.update(
            understood["text"],
            previous_message
        )

        conversation_context = (
            self.gather_conversation_context(
                limit=5
            )
        )

        reasoning = self.reason(
            understood,
            memories,
            experiences,
            goal,
            mode,
            priority,
            conversation_context,
            current_topic
        )

        strategy = self.choose_response_strategy(
            intent,
            reasoning["decision"],
            memories,
            experiences,
            priority
        )

        plan = self.make_plan(
            understood["text"],
            reasoning["decision"]
        )

        advanced_reasoning = reasoning.get("advanced", {})

        if not goal:
            advanced = reasoning.get("advanced", {})
            resolved = advanced.get("resolved", {}) if isinstance(advanced, dict) else {}
            goal = resolved.get("subject") or current_topic or ""

        if goal or current_topic:
            self.goal_state.update(
                goal=goal,
                topic=current_topic or "",
                status="active",
                confidence=reasoning.get("confidence", 0.0)
            )

        # Build a response from Vin's own reasoning.
        # The optional language model is not required.
        response_text = self._build_response(
            understood["text"],
            intent,
            reasoning,
            strategy,
            goal,
            current_topic
        )

        result = CognitiveResult(
            text=response_text,
            intent=intent,
            memories=memories,
            experiences=experiences,
            decision=reasoning["decision"],
            plan=plan,
            confidence=reasoning["confidence"],
            reason=reasoning["reason"],
            goal=goal,
            mode=mode,
            priority=priority,
            response_strategy=strategy
        )
        result.reasoning = advanced_reasoning

        self.last_result = result

        self.conversation.append({
            "user": understood["text"],
            "intent": intent,
            "decision": reasoning["decision"],
            "goal": goal,
            "mode": mode,
            "priority": priority,
            "response_strategy": strategy,
            "experience_matches": len(experiences),
            "time": time.time(),
            "processing_time": time.time() - start,
            "reasoning_confidence": reasoning.get("confidence", 0.0),
            "reasoning_candidates": len(advanced_reasoning.get("candidates", [])) if isinstance(advanced_reasoning, dict) else 0
        })

        self.conversation = self.conversation[-50:]

        self._save_conversation()

        return result

    def status(self):

        return {
            "online": True,
            "conversation_items": len(
                self.conversation
            ),
            "adaptive_learning": (
                self.adaptive_learning is not None
            ),
            "experience_matches": (
                len(
                    self.last_result.experiences
                )
                if self.last_result
                else 0
            ),
            "last_intent": (
                self.last_result.intent
                if self.last_result
                else None
            ),
            "last_decision": (
                self.last_result.decision
                if self.last_result
                else None
            ),
            "last_goal": (
                self.last_result.goal
                if self.last_result
                else None
            ),
            "last_mode": (
                self.last_result.mode
                if self.last_result
                else None
            ),
            "last_priority": (
                self.last_result.priority
                if self.last_result
                else None
            ),
            "last_response_strategy": (
                self.last_result.response_strategy
                if self.last_result
                else None
            )
        }
