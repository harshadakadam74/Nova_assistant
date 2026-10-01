import unittest

from core.ai_engine import GeminiClient


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"candidates": [{"content": {"parts": [{"text": "A concise answer."}]}}]}


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse()


class GeminiClientTests(unittest.TestCase):
    def test_missing_key_disables_network_requests(self):
        session = FakeSession()
        client = GeminiClient(api_key="", session=session)
        self.assertIsNone(client.respond("hello"))
        self.assertEqual(session.calls, [])

    def test_key_is_sent_in_header_with_timeout_and_context_limit(self):
        session = FakeSession()
        client = GeminiClient(api_key="test-key", session=session)

        for index in range(8):
            self.assertEqual(client.respond(f"prompt {index}"), "A concise answer.")

        url, request = session.calls[0]
        self.assertNotIn("test-key", url)
        self.assertEqual(request["headers"]["x-goog-api-key"], "test-key")
        self.assertGreater(request["timeout"], 0)
        self.assertEqual(len(client.history), 12)

    def test_only_explicit_preferences_enter_system_instruction(self):
        session = FakeSession()
        client = GeminiClient(api_key="test-key", session=session)
        client.respond("question", preferences="use metric units")
        instruction = session.calls[0][1]["json"]["system_instruction"]["parts"][0]["text"]
        self.assertIn("use metric units", instruction)


if __name__ == "__main__":
    unittest.main()