import unittest

from core.assistant import Zyra


class DisabledAI:
    enabled = False

    def respond(self, prompt, preferences=""):
        return None


class AssistantResponseTests(unittest.TestCase):
    def setUp(self):
        self.assistant = Zyra(tts=None, ai_client=DisabledAI())

    def test_unconfigured_general_chat_explains_how_to_enable_it(self):
        reply = self.assistant.handle("explain photosynthesis")
        self.assertIn("GEMINI_API_KEY", reply)
        self.assertIn("built-in commands", reply)

    def test_local_commands_work_without_gemini(self):
        reply = self.assistant.handle("what is the time")
        self.assertIn("It's", reply)


if __name__ == "__main__":
    unittest.main()