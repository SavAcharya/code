# Test Strategy — Job Search OS

## Why these tests exist

This codebase has hard, stateful invariants that fail silently if broken. The
strategy targets those invariants first, not coverage percentage. Highest-risk
surface is the LLM router and the cache; both are pure enough to test without a
running Postgres/Redis/Ollama.

## Scope

| Area | Tested | How |
|---|---|---|
| `generator ≠ judge` invariant | ✅ | Mock provider health checks; assert judge is never the generator model |
| Provider fallback chains | ✅ | qwen→gemma generator fallback; Gemini→gemma judge fallback; all-down cases |
| Route config integrity | ✅ | Every route that names a judge declares one distinct from its generator |
| Cache key determinism + format | ✅ | `_hash` is stable, collision-distinct, 20 chars; key is `llm:{task}:{hash}` |
| Cache fault tolerance | ✅ | Redis errors are swallowed, never propagate to callers |
| Resume version auto-deactivation | ⬜ Planned | Needs an async DB fixture (SQLite/Postgres) — next increment |
| Stage-prep generation (M2) | ⬜ Planned | Add when the feature lands |

## Running

```bash
cd backend
pip install pytest pytest-asyncio httpx redis pydantic-settings
pytest                 # asyncio_mode=auto via pytest.ini
```

Current result: **12 passed**.

## The invariant that matters most

`LLMRouter.select_judge` must never return the same model that generated the
content — otherwise the "judge" rubber-stamps its own output and quality scores
are meaningless. The decisive test is
`test_judge_never_equals_generator_when_generator_is_gemma`: with Gemini down and
gemma as the generator, the router must return `(None, "unavailable")` rather
than reusing gemma. If a future refactor breaks this, that test goes red.

## Next increments

1. Async DB fixture → test `Resume` version bump auto-deactivates the prior active row.
2. Contract test on the matcher endpoint: `missing_keywords` always present in the response shape (the field the stage-prep feature depends on).
3. CI: run `pytest` on every push (no CI exists yet — `.github/workflows/test.yml`).
