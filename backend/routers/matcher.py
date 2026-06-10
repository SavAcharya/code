from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Resume
from llm.orchestrator import run

router = APIRouter()


class AnalyzeRequest(BaseModel):
    jd_text: str
    resume_variant: str = "fdl"


@router.post("/analyze")
async def analyze(req: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Resume).where(Resume.variant == req.resume_variant, Resume.is_active == True)
        .order_by(Resume.version.desc())
    )
    resume = result.scalar_one_or_none()
    if not resume:
        return {"error": f"No active resume found for variant '{req.resume_variant}'"}

    response = await run(
        task="matcher.analyze",
        system="You are an expert ATS resume analyzer. Think carefully. Analyse every dimension.",
        prompt=f"Analyze match between JD and resume.\n\nJOB DESCRIPTION:\n{req.jd_text}\n\nRESUME ({req.resume_variant.upper()}):\n{resume.content}\n\nReturn JSON: {{\"match_score\":0,\"verdict\":\"\",\"role_detected\":\"\",\"matched_keywords\":[],\"missing_keywords\":[],\"strengths\":[],\"gaps\":[],\"rewritten_bullets\":[{{\"original\":\"\",\"rewritten\":\"\",\"reason\":\"\"}}],\"tailored_summary\":\"\",\"overall_recommendation\":\"\"}}",
        judge_context=req.jd_text[:800],
        judge_content_type="resume_analysis",
        parse_json=True,
    )

    return {
        "analysis": response.content,
        "judge": response.judge.model_dump() if response.judge else None,
        "meta": {"model_chain": response.model_chain, "generation_ms": response.generation_ms, "cached": response.cached},
    }
