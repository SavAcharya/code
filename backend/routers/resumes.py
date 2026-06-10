from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from database import get_db
from models import Resume

router = APIRouter()


class ResumeCreate(BaseModel):
    variant: str
    label: str = "Custom resume"
    content: str


@router.get("/")
async def list_resumes(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Resume).order_by(Resume.variant, Resume.version.desc()))
    return [{"id": r.id, "variant": r.variant, "version": r.version,
             "label": r.label, "is_active": r.is_active,
             "created_at": r.created_at.isoformat() if r.created_at else None}
            for r in r.scalars().all()]


@router.get("/{variant}/active")
async def get_active(variant: str, db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(Resume).where(Resume.variant == variant, Resume.is_active == True)
        .order_by(Resume.version.desc())
    )
    resume = r.scalar_one_or_none()
    if not resume: raise HTTPException(404, f"No active {variant} resume")
    return {"id": resume.id, "variant": resume.variant, "version": resume.version,
            "label": resume.label, "content": resume.content}


@router.post("/", status_code=201)
async def create_version(p: ResumeCreate, db: AsyncSession = Depends(get_db)):
    # Get max version for this variant
    r = await db.execute(
        select(Resume).where(Resume.variant == p.variant).order_by(Resume.version.desc())
    )
    latest = r.scalar_one_or_none()
    new_version = (latest.version + 1) if latest else 1

    # Deactivate previous
    if latest and latest.is_active:
        latest.is_active = False

    resume = Resume(variant=p.variant, version=new_version, label=p.label,
                    content=p.content, is_active=True)
    db.add(resume)
    await db.flush(); await db.refresh(resume)
    return {"id": resume.id, "variant": resume.variant, "version": resume.version}
