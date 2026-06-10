# Job Search OS v2

LLM-as-Judge job search system with provider abstraction, result caching, and resume versioning.

## Architecture

```
qwen3.6 (:11434)  ──► GENERATOR ──► generates content
                                         │
gemma4 (:11435)   ──► JUDGE FALLBACK     ▼
                                    ┌─────────┐
Gemini API        ──► PRIMARY JUDGE │ Router   │ enforces: generator ≠ judge
                                    └─────────┘
                                         │
Redis             ──► CACHE (24h TTL)    ▼
PostgreSQL        ──► TRACKER + RESUMES (versioned)
```

## Stack

| Layer | Tech | Purpose |
|---|---|---|
| Frontend | Vue 3 + Vite + Pinia | SPA with sidebar nav |
| Backend | FastAPI + Python 3.12 | REST API + orchestrator |
| Generator | qwen3.6 on Ollama :11434 | Content generation |
| Judge (primary) | Gemini 2.0 Flash | Challenge + score + improve |
| Judge (fallback) | gemma4 on Ollama :11435 | When Gemini unavailable |
| Database | PostgreSQL 15 | Applications + versioned resumes |
| Cache | Redis 7 | Content-hash based, 24h TTL |

## Key Design Decisions

**Generator ≠ Judge rule**: The router enforces that the judge must always be a different model from the generator. If both fall back to the same model, the response includes `"quality": "degraded"`.

**Provider abstraction**: Models are behind a `LLMProvider` interface. Swapping qwen for a different generator means changing one line in `.env`.

**Resume versioning**: Resumes live in Postgres with version numbers. Creating a new version auto-deactivates the previous one. The matcher always uses the latest active version.

**Result caching**: SHA-256 hash of (task + system_prompt + user_prompt). Same JD analyzed twice returns instantly from Redis.

## Quick Start

```bash
# 1. Start both Ollama instances
OLLAMA_HOST=0.0.0.0:11434 OLLAMA_ORIGINS="*" ollama serve  # terminal 1
OLLAMA_HOST=0.0.0.0:11435 OLLAMA_ORIGINS="*" ollama serve  # terminal 2

# 2. Configure
cp .env.example .env
# Add your GEMINI_API_KEY (optional — system works without it)

# 3. Launch
docker compose up --build

# 4. Open
open http://localhost:3000
```

## API

```
GET  /health              # Health check
GET  /api/status          # All 3 model statuses

POST /api/discover/suggest   # Company suggestions (MEDIUM)
POST /api/matcher/analyze    # JD analysis with judge (HIGH)
POST /api/cover/generate     # Cover letter with judge (CRITICAL)

GET  /api/tracker/           # List applications
POST /api/tracker/           # Create
PUT  /api/tracker/{id}       # Update
DELETE /api/tracker/{id}     # Delete
GET  /api/tracker/export/csv # Export

GET  /api/resumes/              # List all versions
GET  /api/resumes/{variant}/active  # Get active resume
POST /api/resumes/              # Create new version
```

## Task Routing

| Task | Complexity | Generator | Judge | Auto-improve |
|---|---|---|---|---|
| discover.suggest | MEDIUM | qwen3.6 | — | No |
| matcher.analyze | HIGH | qwen3.6 | Gemini → gemma4 | No |
| matcher.rewrite | HIGH | qwen3.6 | Gemini → gemma4 | Yes (< 7.5) |
| cover.draft | CRITICAL | qwen3.6 | Gemini → gemma4 | Yes (< 7.0) |
