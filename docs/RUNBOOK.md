# Runbook — Job Search OS (local Docker Compose)

Personal single-user deployment. No multi-tenant concerns.

## Prerequisites

- Docker + Docker Compose
- Ollama running locally with the generator and judge-fallback models pulled:
  - generator `qwen3.6` on `:11434`
  - judge fallback `gemma4` on `:11435`
- (Optional) `GEMINI_API_KEY` set for the primary judge. Without it, the system
  falls back to gemma and marks judged output `"quality": "degraded"`.

## Start

```bash
cp .env.example .env        # then fill GEMINI_API_KEY if you have one
docker compose up --build
```

Services: frontend (Vite), backend (FastAPI), PostgreSQL 15, Redis 7.

## Health check

- Backend status: `GET /api/llm/status` → reports qwen / gemma / gemini health.
- If `select_judge` returns `unavailable`, judged tasks degrade — check that
  Gemini key is set OR that the generator is qwen (so gemma can judge).

## Common operations

| Task | Command |
|---|---|
| Run tests | `cd backend && pytest` |
| Seed data | `python backend/seed.py` |
| Tail logs | `docker compose logs -f backend` |
| Flush cache | `docker compose exec redis redis-cli FLUSHALL` |

## Rollback

`docker compose down` then redeploy the previous commit. Data persists in the
`db` volume; resumes are versioned in Postgres so a bad resume edit is recoverable
by reactivating the prior version.
