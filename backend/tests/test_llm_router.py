"""Tests for the hard invariant: the judge must never be the same model as the generator."""
from unittest.mock import AsyncMock
import pytest
from llm.router import LLMRouter, ROUTES, RouteConfig


def _af(value):  # async function returning value
    return AsyncMock(return_value=value)


@pytest.fixture
def router():
    r = LLMRouter()
    # default-construct, then control health via mocks per test
    return r


async def test_gemini_healthy_is_full_quality(router):
    router.gemini = AsyncMock()
    router.gemini.health_check = _af(True)
    provider, quality = await router.select_judge(generator_model_id="ollama-generator/qwen3.6")
    assert provider is router.gemini
    assert quality == "full"


async def test_gemini_down_qwen_generator_falls_back_to_gemma(router):
    router.gemini = None
    router.gemma.health_check = _af(True)
    provider, quality = await router.select_judge(generator_model_id="ollama-generator/qwen3.6")
    assert provider is router.gemma
    assert quality == "degraded"


async def test_judge_never_equals_generator_when_generator_is_gemma(router):
    """THE invariant: Gemini down AND generator is gemma -> no independent judge."""
    router.gemini = None
    router.gemma.health_check = _af(True)  # gemma is healthy but is the generator
    provider, quality = await router.select_judge(generator_model_id="ollama-judge/gemma4:latest")
    assert provider is None
    assert quality == "unavailable"


async def test_no_judge_when_everything_down(router):
    router.gemini = None
    router.gemma.health_check = _af(False)
    provider, quality = await router.select_judge(generator_model_id="ollama-generator/qwen3.6")
    assert provider is None
    assert quality == "unavailable"


async def test_generator_prefers_qwen_then_gemma(router):
    router.qwen.health_check = _af(False)
    router.gemma.health_check = _af(True)
    gen = await router.select_generator()
    assert gen is router.gemma  # fell back


async def test_no_generator_raises(router):
    router.qwen.health_check = _af(False)
    router.gemma.health_check = _af(False)
    with pytest.raises(RuntimeError):
        await router.select_generator()


def test_judge_tasks_declare_distinct_judge():
    """Every route that uses a judge must name a judge distinct from 'none'."""
    for task, cfg in ROUTES.items():
        if cfg.judge is not None:
            assert cfg.judge != cfg.generator, f"{task}: generator==judge in config"
