import json
import time
import logging
import re
from .schemas import LLMResponse, JudgeResult, JudgeVerdict, Complexity
from .router import router
from . import cache

logger = logging.getLogger(__name__)

JUDGE_SYSTEM = """You are a ruthlessly honest senior recruiter with 20 years of experience hiring Principal/Lead engineers and PMs at top AI companies.
Your job is to CHALLENGE, not validate. You are the last defense before the candidate submits.
Scoring: 9-10 exceptional, 7-8 good with minor gaps, 5-6 mediocre, 3-4 weak, 1-2 poor.
Return ONLY valid JSON. No markdown. No preamble."""


async def run(
    task: str,
    system: str,
    prompt: str,
    judge_context: str = "",
    judge_content_type: str = "resume_analysis",
    parse_json: bool = False,
) -> LLMResponse:
    route = router.get_route(task)
    model_chain = []
    start = time.monotonic()

    # ── Check cache ──────────────────────────────────────────────────────
    cache_inputs = (task, system[:100], prompt[:500])
    cached = await cache.get(task, *cache_inputs)
    if cached:
        return LLMResponse(**dict(cached, cached=True))

    # ── No LLM needed ────────────────────────────────────────────────────
    if route.generator == "none":
        return LLMResponse(content="", generator_model="none",
                          complexity=route.complexity, generation_ms=0)

    # ── Generate ─────────────────────────────────────────────────────────
    generator = await router.select_generator()
    model_chain.append(generator.model_id())

    gen_system = system
    if parse_json:
        gen_system += "\nCRITICAL: Return ONLY raw JSON. Start with { or [. No markdown. No text before or after."
    if not route.use_thinking:
        prompt += "\n/no_think"

    raw = await generator.generate(gen_system, prompt)
    content = raw

    if parse_json:
        try:
            clean = re.sub(r"```json\s*", "", raw, flags=re.IGNORECASE)
            clean = re.sub(r"```\s*", "", clean).strip()
            m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", clean)
            content = json.loads(m.group(0) if m else clean)
        except json.JSONDecodeError:
            logger.error(f"JSON parse failed for task {task}")
            content = raw

    # ── Judge ─────────────────────────────────────────────────────────────
    judge_result = None
    if route.judge:
        judge_provider, quality = await router.select_judge(generator.model_id())

        if judge_provider:
            model_chain.append(f"{judge_provider.model_id()} (judge)")

            content_str = json.dumps(content, indent=2) if isinstance(content, (dict, list)) else str(content)
            provide_improved = route.complexity == Complexity.CRITICAL or route.auto_improve
            improvement_instructions = "Provide an improved version addressing all issues." if provide_improved else ""
            improved_content_placeholder = '"full improved version"' if provide_improved else "null"

            judge_prompt = f"""CONTENT TYPE: {judge_content_type}
CONTEXT: {judge_context or prompt[:600]}
GENERATED CONTENT TO JUDGE:
{content_str}

{improvement_instructions}

Return ONLY JSON:
{{"verdict":"PASS|CHALLENGE|FAIL","score":0.0,"feedback":"","specific_issues":[],"improvement_suggestions":[],"improved_content":{improved_content_placeholder}}}"""

            judge_raw = None
            try:
                judge_raw = await judge_provider.generate(JUDGE_SYSTEM, judge_prompt, temperature=0.3)
            except Exception as e:
                logger.error(f"Judge failed: {e}")
                fallback_candidate = None
                if router.fallback and await router.fallback.health_check():
                    if router.fallback.model_id().lower() != generator.model_id().lower():
                        fallback_candidate = router.fallback

                if fallback_candidate is not None and fallback_candidate is not judge_provider:
                    try:
                        judge_provider = fallback_candidate
                        quality = "degraded"
                        logger.warning("Primary judge failed, falling back to configured fallback model as judge")
                        judge_raw = await judge_provider.generate(JUDGE_SYSTEM, judge_prompt, temperature=0.3)
                    except Exception as fallback_error:
                        logger.error(f"Fallback judge failed: {fallback_error}")
                        judge_result = JudgeResult(
                            verdict=JudgeVerdict.CHALLENGE, score=0.0,
                            feedback=f"Judge error: {fallback_error}", model="error", quality="error"
                        )
                else:
                    judge_result = JudgeResult(
                        verdict=JudgeVerdict.CHALLENGE, score=0.0,
                        feedback=f"Judge error: {e}", model="error", quality="error"
                    )

            if judge_raw is not None:
                judge_clean = re.sub(r"```json\s*", "", judge_raw, flags=re.IGNORECASE)
                judge_clean = re.sub(r"```\s*", "", judge_clean).strip()
                jm = re.search(r"(\{[\s\S]*\})", judge_clean)

                jdata = None
                try:
                    jdata = json.loads(jm.group(0) if jm else judge_clean)
                except Exception as je:
                    logger.error(f"Failed to parse judge JSON: {je}; raw: {judge_raw[:2000]}")
                    judge_result = JudgeResult(
                        verdict=JudgeVerdict.CHALLENGE,
                        score=0.0,
                        feedback=f"Judge parse error: {je}",
                        specific_issues=[],
                        improvement_suggestions=[],
                        improved_content=None,
                        model=judge_provider.model_id() if judge_provider else "unknown",
                        quality=quality,
                    )

                if jdata:
                    judge_result = JudgeResult(
                        verdict=JudgeVerdict(jdata.get("verdict", "CHALLENGE")),
                        score=float(jdata.get("score", 5.0)),
                        feedback=jdata.get("feedback", ""),
                        specific_issues=jdata.get("specific_issues", []),
                        improvement_suggestions=jdata.get("improvement_suggestions", []),
                        improved_content=jdata.get("improved_content") if provide_improved else None,
                        model=judge_provider.model_id(),
                        quality=quality,
                    )

                    # Auto-improve if score below threshold
                    if (route.auto_improve and judge_result.score < route.improve_threshold
                            and judge_result.improved_content):
                        logger.info(f"Auto-improve: {task} scored {judge_result.score:.1f} < {route.improve_threshold}")
                        content = judge_result.improved_content
                        model_chain.append("auto-improved")

    total_ms = int((time.monotonic() - start) * 1000)

    result = LLMResponse(
        content=content,
        generator_model=model_chain[0] if model_chain else "unknown",
        complexity=route.complexity,
        generation_ms=total_ms,
        judge=judge_result,
        model_chain=model_chain,
    )

    # Cache successful results
    if judge_result is None or judge_result.verdict != JudgeVerdict.FAIL:
        await cache.set(task, result.model_dump(), *cache_inputs)

    return result
