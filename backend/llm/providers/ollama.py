import re
import json
import httpx
import logging
from .base import LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    def __init__(self, host: str, model: str, name_suffix: str = ""):
        self.host = host.rstrip("/")
        self.model = model
        self.name = f"ollama{name_suffix}"
        self._healthy = None

    async def generate(self, system: str, prompt: str, temperature: float = 0.1) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {"temperature": temperature, "num_ctx": 8192},
        }
        async with httpx.AsyncClient(timeout=180.0) as client:
            r = await client.post(f"{self.host}/v1/chat/completions", json=payload)
            r.raise_for_status()
        raw = r.json()["choices"][0]["message"]["content"]
        return self._strip_think(raw)

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self.host}/api/tags")
                self._healthy = r.status_code == 200
        except Exception:
            self._healthy = False
        return self._healthy

    @staticmethod
    def _strip_think(text: str) -> str:
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()

    @staticmethod
    def parse_json(text: str) -> dict | list:
        clean = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
        clean = re.sub(r"```\s*", "", clean).strip()
        m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", clean)
        return json.loads(m.group(0) if m else clean)
