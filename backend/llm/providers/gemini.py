import re
import json
import logging
from .base import LLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.name = "gemini"
        self._client = None

    def _get_client(self):
        if self._client is None:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
        return self._client

    async def generate(self, system: str, prompt: str, temperature: float = 0.3) -> str:
        client = self._get_client()
        response = client.generate_content(f"{system}\n\n{prompt}")
        return response.text

    async def health_check(self) -> bool:
        return bool(self.api_key)
