from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Resume
from llm.orchestrator import run

router = APIRouter()


class CoverRequest(BaseModel):
    company: str
    role: str
    jd_text: Optional[str] = ""
    resume_variant: str = "fdl"


@router.post("/generate")
async def generate(req: CoverRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Resume).where(Resume.variant == req.resume_variant, Resume.is_active == True)
        .order_by(Resume.version.desc())
    )
    resume = result.scalar_one_or_none()
    resume_text = resume.content if resume else "Resume not found"
    jd = req.jd_text or f"Role: {req.role} at {req.company}"

    response = await run(
        task="cover.draft",
        system="You are an expert cover letter writer for Principal/Lead tech roles. Output ONLY the letter text.",
        prompt=f"Write a cover letter.\n\nROLE: {req.role} at {req.company}\nJD: {jd}\nRESUME ({req.resume_variant.upper()}):\n{resume_text}\n\n3 paragraphs, 280-320 words. Specific hook, 2 quantified achievements, confident CTA. No 'I am excited to apply'. Start with Dear.",
        judge_context=f"Company: {req.company}, Role: {req.role}, JD: {jd[:500]}",
        judge_content_type="cover_letter",
    )

    return {
        "cover_letter": response.content,
        "judge": response.judge.model_dump() if response.judge else None,
        "meta": {"model_chain": response.model_chain, "generation_ms": response.generation_ms, "cached": response.cached},
    }
