import os
import json


class VerificationResult:

    def __init__(
        self,
        success,
        status,
        reason="",
        evidence=None
    ):
        self.success = bool(success)
        self.status = status
        self.reason = reason
        self.evidence = evidence or []

    def to_dict(self):
        return {
            "success": self.success,
            "status": self.status,
            "reason": self.reason,
            "evidence": self.evidence
        }


class VerificationCore:

    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.last_result = None

    def file_exists(self, path):

        path = os.path.abspath(path)

        if os.path.exists(path):
            result = VerificationResult(
                True,
                "VERIFIED",
                "The requested file or directory exists.",
                [path]
            )
        else:
            result = VerificationResult(
                False,
                "FAILED",
                "The requested file or directory does not exist.",
                [path]
            )

        self.last_result = result
        return result

    def json_valid(self, path):

        path = os.path.abspath(path)

        if not os.path.exists(path):
            result = VerificationResult(
                False,
                "FAILED",
                "The JSON file does not exist.",
                [path]
            )
            self.last_result = result
            return result

        try:
            with open(path, "r", encoding="utf-8") as f:
                json.load(f)

            result = VerificationResult(
                True,
                "VERIFIED",
                "The JSON file is valid.",
                [path]
            )

        except Exception as error:
            result = VerificationResult(
                False,
                "FAILED",
                "The JSON file could not be parsed.",
                [str(error)]
            )

        self.last_result = result
        return result

    def text_contains(self, path, expected):

        path = os.path.abspath(path)

        if not os.path.exists(path):
            result = VerificationResult(
                False,
                "FAILED",
                "The target file does not exist.",
                [path]
            )
            self.last_result = result
            return result

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            found = str(expected).casefold() in content.casefold()

            if found:
                result = VerificationResult(
                    True,
                    "VERIFIED",
                    "The expected text was found.",
                    [str(expected)]
                )
            else:
                result = VerificationResult(
                    False,
                    "FAILED",
                    "The expected text was not found.",
                    [str(expected)]
                )

        except Exception as error:
            result = VerificationResult(
                False,
                "FAILED",
                "The file could not be inspected.",
                [str(error)]
            )

        self.last_result = result
        return result

    def verify_result(self, result):
        """
        Verify common result types.

        Supports:
        - None
        - bool
        - strings containing clear success indicators
        - structured dictionaries with explicit success/status/message fields

        Unknown result types remain UNCERTAIN rather than being trusted.
        """

        if result is None:

            verified = VerificationResult(
                False,
                "UNKNOWN",
                "There was no result to verify."
            )

        elif isinstance(result, bool):

            verified = VerificationResult(
                result,
                "VERIFIED" if result else "FAILED",
                "Boolean result received."
            )

        elif isinstance(result, str):

            success_words = (
                "success",
                "successful",
                "opened",
                "created",
                "saved",
                "done",
                "completed",
                "verified"
            )

            lower = result.casefold()

            success = any(
                word in lower
                for word in success_words
            )

            verified = VerificationResult(
                success,
                "VERIFIED" if success else "UNCERTAIN",
                "Result text was evaluated.",
                [result]
            )

        elif isinstance(result, dict):

            # Explicit boolean success is strongest evidence.
            if isinstance(result.get("success"), bool):

                success = result["success"]

                verified = VerificationResult(
                    success,
                    "VERIFIED" if success else "FAILED",
                    "Structured result contained an explicit success value.",
                    [result]
                )

            else:

                status = str(
                    result.get("status", "")
                ).casefold().strip()

                message = str(
                    result.get("message", "")
                ).casefold().strip()

                # Explicit verified/success status.
                if status in (
                    "verified",
                    "success",
                    "successful",
                    "completed",
                    "done"
                ):

                    verified = VerificationResult(
                        True,
                        "VERIFIED",
                        "Structured result reported a successful status.",
                        [status]
                    )

                else:

                    success_words = (
                        "success",
                        "successful",
                        "completed",
                        "complete",
                        "done",
                        "verified"
                    )

                    message_success = any(
                        word in message
                        for word in success_words
                    )

                    # A structured result with a clear completion
                    # message is accepted as verified evidence.
                    if message_success:

                        verified = VerificationResult(
                            True,
                            "VERIFIED",
                            "Structured result contained a clear successful completion message.",
                            [result]
                        )

                    else:

                        verified = VerificationResult(
                            False,
                            "UNCERTAIN",
                            "The structured result requires deeper verification.",
                            [result]
                        )

        else:

            verified = VerificationResult(
                False,
                "UNCERTAIN",
                "The result type requires deeper verification."
            )

        self.last_result = verified
        return verified

    def status(self):

        return {
            "online": True,
            "last_status": (
                self.last_result.status
                if self.last_result
                else None
            ),
            "last_success": (
                self.last_result.success
                if self.last_result
                else None
            )
        }
