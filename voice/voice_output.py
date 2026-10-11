import subprocess


class VoiceOutput:
    """Fast Android TTS output for Vin."""

    def __init__(self, rate=0.85, pitch=0.75):
        self.rate = rate
        self.pitch = pitch

    def speak(self, text):
        text = str(text).strip()

        if not text:
            return False

        try:
            subprocess.Popen(
                [
                    "termux-tts-speak",
                    "-r", str(self.rate),
                    "-p", str(self.pitch),
                    "-s", "MUSIC",
                    text,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            return True

        except Exception as exc:
            print("[TTS ERROR]", exc)
            return False


if __name__ == "__main__":
    voice = VoiceOutput()

    print("VIN VOICE OUTPUT")
    print("----------------")

    voice.speak(
        "Hello. I am Vin, your personal butler."
    )

    print("TTS started immediately.")
