from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, get_db, AsyncSessionLocal
from models import Application, Profile, Resume  # noqa: registers models
from routers import discover, matcher, profile as profile_router, tracker, cover, resumes as resumes_router
from seed import seed_resumes
from llm.router import router as llm_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed resumes on first run
    async with AsyncSessionLocal() as db:
        await seed_resumes(db)
    yield


app = FastAPI(title="Job Search OS", version="2.0.0",
              description="LLM-as-Judge: qwen3.6 (gen) + Gemini/gemma4 (judge)", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(discover.router, prefix="/api/discover", tags=["Discover"])
app.include_router(matcher.router, prefix="/api/matcher", tags=["Matcher"])
app.include_router(tracker.router, prefix="/api/tracker", tags=["Tracker"])
app.include_router(profile_router.router, prefix="/api/profile", tags=["Profile"])
app.include_router(cover.router, prefix="/api/cover", tags=["Cover Letter"])
app.include_router(resumes_router.router, prefix="/api/resumes", tags=["Resumes"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/status")
async def status():
    return await llm_router.get_status()
