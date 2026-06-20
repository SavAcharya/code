# Implementation Brief: Rebuild Discovery as a Goal-Driven Agent

**For:** the implementing Claude coding agent
**Repo:** `JOB Search/code` (FastAPI backend + Vue 3 frontend)
**Author of brief:** architecture review pass
**Status:** ready to implement. Read the whole brief before writing code.

---

## 0. TL;DR — what's actually wrong

The Discovery page **does not search for jobs**. It never has. Every symptom the user reported is downstream of one fact:

`POST /discover/suggest` asks an LLM (qwen) to *imagine* 6 companies from a hardcoded profile string. It fetches no real listings, no real JDs, and produces `careers_url` values the model invented (frequently wrong/hallucinated). There is no scoring at discovery, so there is nothing to filter on. When the user clicks **Match JD**, the frontend injects the literal placeholder string `"Paste the job description from their careers page here."` as the fake JD — which is why the Matcher tells the user to paste a JD that the system supposedly "already has."

So this is not a set of small bugs. It is a missing capability (real job + JD retrieval) plus a non-agentic one-shot pipeline. Fix the capability first; the rest collapses out of it.

There is already an **unused MCP server** in the environment exposing `search_jobs`, `get_job_details`, `get_company_data`, `get_resume`. This is the intended-but-unwired real data source. Use it.

---

## 1. Product decisions (already made — do not relitigate)

1. **Data source: agent decides per-case.** The orchestrator tries the `search_jobs` MCP first for real listings + `get_job_details` for real JD text; falls back to fetching/parsing the JD URL when MCP has no hit; only falls back to LLM reasoning when neither is available (and must label such results as *unverified*).
2. **Goal-driven agent.** Discovery is a goal the agent pursues ("find N qualified, real, scored targets matching the user's profile and stated constraints"), not a single request/response. The agent plans, searches, fetches, scores, filters, and decides whether to search again or stop — it owns the course to the goal.
3. **Two-tier scoring.** A cheap pre-screen ranks candidates (role-title / keyword / fast-model heuristic). Full LLM match-scoring runs only on the top N survivors. Anything below a configurable threshold is filtered out *before* it reaches the user.

---

## 2. Architect's guardrails (build these in even though autonomy is high)

The user asked for a goal-driven agent that decides its own course. Honor that, but a fully unbounded loop over paid LLM calls + external fetches is a cost and correctness hazard. Non-negotiable guardrails:

- **Bounded loop:** hard caps on iterations (e.g. `max_search_rounds`, `max_jobs_scored`, `max_wallclock_s`, `max_cost_tokens`). The agent decides *within* the budget; it cannot exceed it.
- **Human checkpoint before any external/destructive side effect.** The agent may search, fetch, score, and filter autonomously. It must **not** auto-save to the tracker or take any apply-like action without explicit user confirmation. Surfacing qualified targets = autonomous; persisting/acting = gated.
- **No silent hallucination.** Any result not backed by a real fetched JD must carry a `verified: false` flag and be visually marked. Never present an invented `careers_url` as if confirmed.
- **Every agent decision is observable.** Stream the agent's plan/steps to the UI (you already have `ThinkingBar` and a `model_chain` meta pattern — extend it into a step log). The user must be able to see *why* a target was kept or dropped.

If you disagree with any guardrail, leave a comment and proceed with it anyway; do not remove it.

---

## 3. Symptom → root cause → fix (the honest review)

| # | User-reported symptom | Root cause (file) | Fix |
|---|---|---|---|
| 1 | "How do I search? It only offers Save / Cancel." | `DiscoverView.vue` has no search input — only a role-type `<select>` and a "Suggest targets" button. `discover.py` exposes only `/suggest`. | Add a real goal/search input (role, optional company list, location, remote, seniority, free-text intent, optional JD URL). Drive the agent endpoint from it. |
| 2 | "Add manually doesn't work / can't add something new." | `saveManual()` does `if (!manual.value.role) return` — silent no-op when role is blank, no validation feedback. It also writes to the **tracker** (`store.createApplication`), not to the discovery list, and surfaces no success/error. | Validate with inline messages; on success show confirmation; decide intended destination (add as a discovery card AND/OR tracker) and make it explicit. Surface failures. |
| 3 | "Suggest targets is one-time, won't search deeper, always 6." | Prompt hardcodes *"suggest 6 companies"*; Redis cache keys on SHA-256 of (task+system+prompt), so re-clicking returns the **identical cached** result instantly. (`discover.py`, `llm/cache.py`) | Replace with the agentic loop that can go deeper (more rounds, new sources, broadened queries). Make result count dynamic. Add cache-bust / "search deeper" that varies the query so the hash changes, or bypass cache for explicit re-search. |
| 4 | "Match JD shows 'paste the JD here' — system should already have it." | `goMatch()` sets `sessionStorage.prefill_jd` to the literal placeholder string. Discovery never retrieved a JD, so there is nothing to pass. | Once Discovery fetches real JD text (via MCP/URL), store and pass the actual JD to the Matcher. The Matcher should open pre-populated and read-only-by-default, editable on demand. |
| 5 | "Why am I shown a 4/10 match at all? Filter it at discovery." | Discovery does zero scoring; scoring only happens in `matcher.py` *after* manual paste. No score exists at discovery time, so nothing can be filtered. | Two-tier scoring at discovery (§1.3). Filter below `min_match_threshold` before presenting. Show the score on each surviving card. |
| 6 | "JD match returned 'search parser error.'" | `orchestrator.run(..., parse_json=True)` throws on malformed LLM JSON; the raw error bubbles to the UI. No retry, no schema repair, no fallback. Frontend has a single red `<p>` for all errors. | Add robust JSON handling: schema-validated parse, one repair retry, typed error envelope. Build a real error-handling layer end to end (see §6). |
| 7 | "Make it a true agentic platform — it decides and moves forward, not a sequential workflow." | Entire pipeline is one-shot request/response. The "judge" only scores; it drives no decisions or next actions. | Introduce the goal-driven orchestrator (§4). |

---

## 4. Target architecture

### 4.1 New backend: a Discovery agent (orchestrator loop)

Create `backend/agents/discovery_agent.py` (or `routers/discover.py` rewritten to delegate to it). The agent runs a bounded plan→act→observe loop toward an explicit goal.

```
GOAL: find up to N real, verified, scored targets matching {profile, constraints}
      with match_score >= min_threshold, within {budget caps}.

LOOP (until goal met OR budget exhausted):
  1. PLAN     → decide next action: search MCP, fetch JD URL, broaden query,
                deep-score a shortlisted candidate, or stop.
  2. SEARCH   → search_jobs(MCP) with current query; collect candidates.
  3. ENRICH   → for each candidate, get_job_details(MCP) or fetch+parse JD URL
                to obtain REAL jd_text. Mark verified=true. If neither works,
                keep as verified=false (LLM-reasoned) or drop.
  4. PRESCREEN→ cheap rank (role-title/keyword/fast model). Keep top K.
  5. SCORE    → full matcher.analyze on top K (reuse existing matcher logic).
  6. FILTER   → drop score < min_threshold.
  7. DECIDE   → enough qualified targets? stop. else broaden/search again
                (respecting iteration + cost caps).
EMIT: ranked qualified targets, each with {company, role, location, jd_text,
      match_score, verdict, verified, source, why_fit, careers_url, step_trace}.
```

Reuse, don't duplicate: the scoring step should call the **same** logic as `matcher.py /analyze` (extract it into a shared service so Discovery and the Matcher page share one code path).

### 4.2 New / changed endpoints

- `POST /discover/run` — body: `{ goal_text?, role_type?, companies?[], location?, remote?, seniority?, jd_url?, max_targets?, min_match_threshold? }`. Returns qualified, scored, verified targets + an agent step trace + meta. Supports **streaming** (SSE or chunked) so the UI shows live progress; this is also the "search deeper" path (call again with broadened params / cache bypass).
- `POST /discover/fetch-jd` — body `{ url }` → `{ jd_text, source, verified }`. Server-side fetch + parse of a JD page (the user explicitly asked how a pasted JD URL should work). Sanitize/normalize to plain text.
- Keep `POST /matcher/analyze` but have Discovery reuse its core service.
- Deprecate the old hallucinate-only `/discover/suggest` (or keep it behind a `verified:false` "ideas" mode, clearly labelled).

### 4.3 Frontend (`DiscoverView.vue`)

- Replace the role-only control with a **goal/search panel**: free-text intent + structured fields (role, companies, location, remote, seniority, JD URL) + `max_targets` and `min_match` controls.
- Render the **agent step trace** live (extend `ThinkingBar` into a step log: "searching board… fetched 14… enriched 9 JDs… scored top 6… dropped 3 below 60%").
- Each result card shows: real match score (badge), `verified` indicator, source, and a **Match JD** button that passes the **real** `jd_text` to the Matcher (no placeholder).
- Fix **Add manually**: inline validation, success/error feedback, explicit destination. A manually added item with a JD URL should trigger `fetch-jd` + scoring so it's treated like any other candidate.
- Replace the single red `<p>` with a proper error/empty/loading state set (see §6).

### 4.4 Caching

Keep Redis caching for deterministic sub-calls (a given JD+resume analysis can stay cached — that's a feature). But the **agent loop and explicit "search deeper" must be able to bypass or vary the cache** so re-running actually explores. Key agent-level results on a query fingerprint that includes a round/nonce when the user asks to go deeper.

---

## 5. Two-tier scoring detail

- **Tier 1 — pre-screen (cheap, fast, runs on all candidates):** role-title match + keyword overlap between JD and the active resume, optionally a single fast-model pass. Produces a cheap rank. No expensive judge calls here.
- **Tier 2 — deep score (expensive, runs on top K only):** the existing `matcher.analyze` path (generator + Gemini judge). Produces the real `match_score`, verdict, gaps, rewrites.
- **Filter** below `min_match_threshold` (default e.g. 60/100; user-adjustable) before anything reaches the UI. Surviving cards display the deep score. Cap K (e.g. 6–8) to bound cost.

This is the explicit compromise for the user's "don't show me 4/10 options": you cannot know a score without a JD + an LLM pass, so you fetch + cheaply rank everything but only pay for deep scoring on the likely winners.

---

## 6. Error handling (currently absent — build it properly)

- **Backend:** wrap LLM JSON parsing in schema validation (Pydantic) + **one repair retry** (feed the malformed output back asking for valid JSON) + typed fallback. Never let a parser exception reach the client raw. Return a consistent error envelope `{ error: { code, message, retryable } }`. Handle MCP timeouts, JD-fetch failures (paywalls, 403, JS-rendered pages), and judge-unavailable degradation (you already have a `quality:"degraded"` concept — surface it).
- **Frontend:** distinct UI states for loading / streaming-progress / empty / partial-success / error-retryable / error-fatal. Per-card error states (one JD failing to fetch must not kill the whole run). Show actionable messages, not raw stack strings. The "search parser error" the user hit must become a graceful, retryable state.

---

## 7. Suggested build order

1. **Wire real data first.** `search_jobs` + `get_job_details` MCP integration and `POST /discover/fetch-jd`. Prove you can get real JD text end to end. *Everything depends on this.*
2. Extract shared **scoring service** from `matcher.py`; add **Tier-1 pre-screen**.
3. Build the **bounded agent loop** (`/discover/run`) with budget caps + step trace.
4. **Frontend**: goal/search panel, live step trace, real-JD handoff to Matcher, fixed "Add manually", full error/empty/loading states.
5. **Error-handling layer** (JSON repair, typed envelopes, MCP/fetch failure paths) — bake in alongside 1–4, then harden.
6. **Caching**: cache-bust / "search deeper" semantics.
7. Tests (§8).

---

## 8. Acceptance criteria (definition of done)

- [ ] Searching a role/goal returns **real** listings with **real** JD text fetched from MCP or the live URL; no invented `careers_url` presented as verified.
- [ ] "Search deeper" / re-running explores further instead of returning the identical cached 6.
- [ ] Clicking **Match JD** opens the Matcher **pre-filled with the actual JD** — never the placeholder string.
- [ ] Discovery shows a real two-tier match score per card and **filters out anything below the threshold** before display.
- [ ] **Add manually** validates, gives success/error feedback, routes to the intended destination, and (with a JD URL) scores the item like any other.
- [ ] A malformed-LLM-JSON or failed JD fetch produces a **graceful, retryable** UI state — never "search parser error" raw.
- [ ] The agent pursues the goal autonomously within hard budget caps, streams its step trace, and stops on its own when the goal is met — but **never persists to the tracker or acts externally without user confirmation**.
- [ ] Tests cover: agent loop termination/caps, JSON repair retry, JD-fetch failure paths, two-tier filtering threshold, MCP-unavailable fallback.

---

## 9. Key files to touch

```
backend/routers/discover.py        # rewrite: delegate to agent; deprecate /suggest
backend/agents/discovery_agent.py  # NEW: bounded goal-driven loop
backend/services/scoring.py        # NEW: shared two-tier scoring (extracted from matcher)
backend/routers/matcher.py         # refactor to use shared scoring service
backend/services/jd_fetch.py       # NEW: fetch + parse JD from URL
backend/integrations/jobs_mcp.py   # NEW: wrap search_jobs / get_job_details / get_company_data
backend/llm/orchestrator.py        # add schema-validated parse + repair retry + typed errors
backend/llm/cache.py               # add cache-bust / round-aware keying for "search deeper"
frontend/src/views/DiscoverView.vue# goal/search panel, step trace, real-JD handoff, fix Add-manually, error states
frontend/src/views/MatcherView.vue # accept real prefilled JD; editable-on-demand
frontend/src/api/index.js          # add discover.run (stream), discover.fetchJd
frontend/src/components/ThinkingBar.vue # extend into a live agent step log
```

## 10. Open questions for the implementer to confirm with the user

- Exact `min_match_threshold` default and whether it's user-adjustable per search.
- Whether "Add manually" should land in Discovery, the Tracker, or both.
- Budget caps (max jobs scored per run, wall-clock, token ceiling).
- Which jobs the `search_jobs` MCP actually covers (geography/board) — verify its real response shape before building the parser around assumptions.
