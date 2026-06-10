"""Cache key determinism + format."""
import json
from unittest.mock import AsyncMock
import pytest
import llm.cache as cache


def test_hash_is_deterministic():
    assert cache._hash("a", "b", "c") == cache._hash("a", "b", "c")


def test_hash_differs_on_different_inputs():
    assert cache._hash("a", "b") != cache._hash("a", "c")


def test_hash_length_is_20():
    assert len(cache._hash("x")) == 20


async def test_get_builds_expected_key_and_parses_json(monkeypatch):
    captured = {}
    fake = AsyncMock()
    async def fake_get(key):
        captured["key"] = key
        return json.dumps({"ok": True})
    fake.get = fake_get
    async def fake_redis():
        return fake
    monkeypatch.setattr(cache, "_get_redis", fake_redis)

    result = await cache.get("matcher.analyze", "jd-text", "resume-text")
    assert result == {"ok": True}
    assert captured["key"].startswith("llm:matcher.analyze:")
    assert captured["key"] == f"llm:matcher.analyze:{cache._hash('jd-text','resume-text')}"


async def test_get_swallows_errors(monkeypatch):
    async def boom():
        raise RuntimeError("redis down")
    monkeypatch.setattr(cache, "_get_redis", boom)
    assert await cache.get("t", "x") is None  # must not raise
