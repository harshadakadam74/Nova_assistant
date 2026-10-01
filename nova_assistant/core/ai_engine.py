"""Optional Gemini chat integration. It returns text only and cannot invoke tools."""
import logging

import requests

from config import GEMINI_API_KEY, GEMINI_HISTORY_TURNS, GEMINI_MODEL, GEMINI_TIMEOUT

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self, api_key=None, model=None, session=None):
        self.api_key = GEMINI_API_KEY if api_key is None else api_key
        self.model = model or GEMINI_MODEL
        self.session = session or requests
        self.history = []

    @property
    def enabled(self):
        return bool(self.api_key)

    def respond(self, prompt, preferences=""):
        if not self.enabled or not prompt.strip():
            return None

        contents = [
            {"role": role, "parts": [{"text": text}]}
            for role, text in self.history
        ]
        contents.append({"role": "user", "parts": [{"text": prompt}]})
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        instruction = (
            "You are Zyra, a concise personal assistant. "
            "Answer naturally in English, Hindi, or Marathi, "
            "matching the user's language. You cannot operate "
            "the user's computer or claim to have performed actions."
        )
        if preferences:
            instruction += f" User-approved preferences: {preferences}"

        payload = {
            "system_instruction": {
                "parts": [{"text": instruction}]
            },
            "contents": contents,
        }

        try:
            response = self.session.post(
                url,
                headers={"x-goog-api-key": self.api_key},
                json=payload,
                timeout=GEMINI_TIMEOUT,
            )
            response.raise_for_status()
            answer = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as error:
            logger.warning("Gemini request failed (%s)", type(error).__name__)
            return None

        if not answer:
            return None

        self.history.extend((("user", prompt), ("model", answer)))
        self.history = self.history[-GEMINI_HISTORY_TURNS * 2:]
        return answer