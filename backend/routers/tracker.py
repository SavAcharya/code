from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Application
import io, csv

router = APIRouter()


class AppCreate(BaseModel):
    company: Optional[str] = ""
    role: str
    location: Optional[str] = ""
    url: Optional[str] = ""
    status: str = "Saved"
    match_score: Optional[int] = None
    resume_variant: str = "fdl"
    notes: Optional[str] = ""
    jd_text: Optional[str] = ""
    rewritten_resume: Optional[str] = None


class AppUpdate(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    match_score: Optional[int] = None
    notes: Optional[str] = None
    rewritten_resume: Optional[str] = None


def _s(a):
    return {"id": a.id, "company": a.company or "", "role": a.role, "location": a.location or "",
            "url": a.url or "", "status": a.status, "match_score": a.match_score,
            "resume_variant": a.resume_variant, "notes": a.notes or "", "jd_text": a.jd_text or "",
            "rewritten_resume": a.rewritten_resume or "", "rewritten_at": a.rewritten_at.isoformat() if a.rewritten_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else None}


@router.get("/")
async def list_apps(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Application).order_by(Application.created_at.desc()))
    return [_s(a) for a in r.scalars().all()]


@router.post("/", status_code=201)
async def create_app(p: AppCreate, db: AsyncSession = Depends(get_db)):
    payload = p.model_dump(exclude_none=True)
    if "rewritten_resume" in payload and payload["rewritten_resume"]:
        payload["rewritten_at"] = datetime.utcnow()
    a = Application(**payload)
    db.add(a); await db.flush(); await db.refresh(a)
    return _s(a)


@router.put("/{id}")
async def update_app(id: int, p: AppUpdate, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Application).where(Application.id == id))
    a = r.scalar_one_or_none()
    if not a: raise HTTPException(404)
    payload = p.model_dump(exclude_none=True)
    if "rewritten_resume" in payload and payload["rewritten_resume"]:
        a.rewritten_at = datetime.utcnow()
    for k, v in payload.items(): setattr(a, k, v)
    await db.flush(); await db.refresh(a)
    return _s(a)


@router.delete("/{id}", status_code=204)
async def delete_app(id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Application).where(Application.id == id))
    a = r.scalar_one_or_none()
    if not a: raise HTTPException(404)
    await db.delete(a)


@router.get("/export/csv")
async def export_csv(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Application).order_by(Application.created_at.desc()))
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Company", "Role", "Status", "Match Score", "Resume", "Date", "URL"])
    for a in r.scalars().all():
        w.writerow([a.company, a.role, a.status, f"{a.match_score}%" if a.match_score else "-",
                     a.resume_variant.upper(), a.created_at.strftime("%d/%m/%Y") if a.created_at else "", a.url])
    out.seek(0)
    return StreamingResponse(iter([out.getvalue()]), media_type="text/csv",
                            headers={"Content-Disposition": "attachment; filename=job_tracker.csv"})
