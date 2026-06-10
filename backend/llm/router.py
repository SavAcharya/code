import logging
from dataclasses import dataclass
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
        self.base = OllamaProvider(
            host=settings.ollama_base_host,
            model=settings.base_model,
            name_suffix="-base"
        )
        self.fallback = OllamaProvider(
            host=settings.ollama_fallback_host,
            model=settings.fallback_model,
            name_suffix="-fallback"
        )
        self.qwen = self.base
        self.gemma = self.fallback

        self.gemini = GeminiProvider(
            api_key=settings.gemini_api_key,
            model=settings.judge_model
        ) if settings.judge_provider == "gemini" and settings.gemini_api_key else None

        self.judge = None
        if settings.judge_provider == "ollama":
            self.judge = OllamaProvider(
                host=settings.ollama_judge_host,
                model=settings.judge_model,
                name_suffix="-judge"
            )
        elif settings.judge_provider == "gemini":
            self.judge = self.gemini

    def get_route(self, task: str) -> RouteConfig:
        return ROUTES.get(task, RouteConfig("qwen", "judge", Complexity.HIGH, True, False))

    async def select_generator(self) -> LLMProvider:
        """Primary: base model. Fallback: configured fallback model."""
        if await self.base.health_check():
            return self.base
        logger.warning("Base generator unhealthy, falling back to configured fallback model")
        if await self.fallback.health_check():
            return self.fallback
        raise RuntimeError("No healthy generator available")

    async def select_judge(self, generator_model_id: str) -> tuple[Optional[LLMProvider], str]:
        """
        Primary: configured judge model. Falls back to the configured fallback model only if independent.
        Returns (provider, quality) where quality is "full" or "degraded".
        """
        if self.judge and await self.judge.health_check():
            if self.judge.model_id().lower() != generator_model_id.lower():
                return self.judge, "full"
            logger.warning("Configured judge model matches generator model; cannot use it")

        if self.fallback and await self.fallback.health_check():
            if self.fallback.model_id().lower() != generator_model_id.lower():
                logger.warning("Using configured fallback model as judge because judge model is unavailable or invalid")
                return self.fallback, "degraded"

        logger.error(
            "No independent judge available. Generator=%s, Judge=%s, Fallback=%s",
            generator_model_id,
            self.judge.model_id() if self.judge else "none",
            self.fallback.model_id(),
        )
        return None, "unavailable"

    async def get_status(self) -> dict:
        return {
            "base": {
                "host": settings.ollama_base_host,
                "model": settings.base_model,
                "healthy": await self.base.health_check()
            },
            "fallback": {
                "host": settings.ollama_fallback_host,
                "model": settings.fallback_model,
                "healthy": await self.fallback.health_check()
            },
            "judge": {
                "provider": settings.judge_provider,
                "model": settings.judge_model,
                "healthy": await self.judge.health_check() if self.judge else False,
            },
            "gemini": {
                "enabled": bool(settings.gemini_api_key),
                "model": settings.gemini_model,
            },
        }


# Singleton
router = LLMRouter()
