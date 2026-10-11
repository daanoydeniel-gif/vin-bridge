class ActionLoop:

    def __init__(self, verification, learning=None):
        self.verification = verification
        self.learning = learning
        self.last_result = None

    def execute_and_verify(self, action, description="action"):
        try:
            result = action()

            verification = self.verification.verify_result(result)

            self.last_result = {
                "action": description,
                "result": result,
                "verification": verification.to_dict()
            }

            if self.learning:
                status = verification.status
                self.learning.observe(
                    f"action:{description}:{status}"
                )

            return self.last_result

        except Exception as error:
            self.last_result = {
                "action": description,
                "result": None,
                "verification": {
                    "success": False,
                    "status": "FAILED",
                    "reason": str(error),
                    "evidence": []
                }
            }

            if self.learning:
                self.learning.observe(
                    f"action:{description}:FAILED"
                )

            return self.last_result

    def status(self):
        return {
            "online": True,
            "last_action": (
                self.last_result["action"]
                if self.last_result else None
            ),
            "last_status": (
                self.last_result["verification"]["status"]
                if self.last_result else None
            )
        }
