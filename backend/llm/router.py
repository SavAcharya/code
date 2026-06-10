import logging
from dataclasses import dataclass, field
from typing import Optional
from .schemas import Complexity, Role
from .providers import LLMProvider, OllamaProvider, GeminiProvider
from config import settings

logger = logging.getLogger(__name__)


@dataclass
class RouteConfig:
    generator: str
    judge: Optional[str]
    complexity: Complexity
    use_thinking: bool
    auto_improve: bool
    improve_threshold: float = 7.0


ROUTES: dict[str, RouteConfig] = {
    "tracker.crud":           RouteConfig("none",   None,     Complexity.LOW,      False, False),
    "discover.suggest":       RouteConfig("qwen",   None,     Complexity.MEDIUM,   True,  False),
    "matcher.analyze":        RouteConfig("qwen",   "judge",  Complexity.HIGH,     True,  False),
    "matcher.rewrite":        RouteConfig("qwen",   "judge",  Complexity.HIGH,     True,  True,  7.5),
    "summary.tailor":         RouteConfig("qwen",   "judge",  Complexity.HIGH,     True,  True,  7.5),
    "cover.draft":            RouteConfig("qwen",   "judge",  Complexity.CRITICAL, True,  True,  7.0),
}


class LLMRouter:
    """
    Role-based model selection with fallback chains.
    Hard rule: generator and judge must NEVER be the same model in the same call.
    """

    def __init__(self):
        self.qwen = OllamaProvider(
            host=settings.ollama_generator_host,
            model=settings.ollama_generator_model,
            name_suffix="-generator"
        )
        self.gemma = OllamaProvider(
            host=settings.ollama_judge_host,
            model=settings.ollama_judge_model,
            name_suffix="-judge"
        )
        self.gemini = GeminiProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model
        ) if settings.gemini_api_key else None

    def get_route(self, task: str) -> RouteConfig:
        return ROUTES.get(task, RouteConfig("qwen", "judge", Complexity.HIGH, True, False))

    async def select_generator(self) -> LLMProvider:
        """Primary: qwen. Fallback: gemma."""
        if await self.qwen.health_check():
            return self.qwen
        logger.warning("qwen unhealthy, falling back to gemma as generator")
        if await self.gemma.health_check():
            return self.gemma
        raise RuntimeError("No healthy generator available")

    async def select_judge(self, generator_model_id: str) -> tuple[LLMProvider, str]:
        """
        Primary: Gemini. Fallback: gemma (if generator wasn't gemma).
        Returns (provider, quality) where quality is "full" or "degraded".
        """
        # Try Gemini first — always independent from Ollama generators
        if self.gemini and await self.gemini.health_check():
            return self.gemini, "full"

        # Fallback to gemma — but ONLY if generator wasn't gemma
        if "gemma" not in generator_model_id.lower():
            if await self.gemma.health_check():
                logger.warning("Gemini unavailable, using gemma as judge (different from generator)")
                return self.gemma, "degraded"

        # Last resort: log and return None
        logger.error(
            "No independent judge available. Generator=%s, Gemini=%s, Gemma=%s",
            generator_model_id,
            "no key" if not self.gemini else "unhealthy",
            "same as generator" if "gemma" in generator_model_id.lower() else "unhealthy"
        )
        return None, "unavailable"

    async def get_status(self) -> dict:
        return {
            "qwen": {"host": settings.ollama_generator_host, "model": settings.ollama_generator_model,
                     "healthy": await self.qwen.health_check()},
            "gemma": {"host": settings.ollama_judge_host, "model": settings.ollama_judge_model,
                     "healthy": await self.gemma.health_check()},
            "gemini": {"model": settings.gemini_model,
                      "healthy": await self.gemini.health_check() if self.gemini else False,
                      "enabled": bool(settings.gemini_api_key)},
        }


# Singleton
router = LLMRouter()
