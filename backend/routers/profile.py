from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Profile, Resume
import io
import os
import subprocess
from pathlib import Path
from pypdf import PdfReader
from docx import Document

router = APIRouter()


class ProfileData(BaseModel):
    linkedin_url: str = ""
    active_resume_variant: str = "fdl"
    active_resume_label: str | None = None
    active_resume_content: str | None = None


class ProfileUpdate(BaseModel):
    linkedin_url: str = ""
    active_resume_variant: str = "fdl"


class ResumeUpload(BaseModel):
    variant: str = "fdl"
    label: str = "Uploaded resume"
    content: str


async def _get_profile(db: AsyncSession) -> Profile | None:
    r = await db.execute(select(Profile).limit(1))
    return r.scalar_one_or_none()


async def _get_active_resume(db: AsyncSession, variant: str) -> Resume | None:
    r = await db.execute(
        select(Resume).where(Resume.variant == variant, Resume.is_active == True).order_by(Resume.version.desc())
    )
    return r.scalar_one_or_none()


async def _parse_resume_file(file: UploadFile) -> str:
    filename = file.filename or "resume"
    ext = Path(filename).suffix.lower()
    data = await file.read()

    if ext == ".txt":
        return data.decode("utf-8", errors="replace")

    if ext == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        text_parts = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(text_parts).strip()

    if ext in {".docx"}:
        document = Document(io.BytesIO(data))
        return "\n".join([p.text for p in document.paragraphs]).strip()

    if ext == ".doc":
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            result = subprocess.run(["antiword", tmp_path], capture_output=True, text=True)
            if result.returncode != 0:
                raise HTTPException(status_code=400, detail="Failed to parse .doc file")
            return result.stdout.strip()
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    raise HTTPException(status_code=400, detail="Unsupported resume file type. Use .txt, .pdf, .doc, or .docx.")


@router.get("/")
async def get_profile(db: AsyncSession = Depends(get_db)):
    profile = await _get_profile(db)
    if not profile:
        return ProfileData()

    active_resume = await _get_active_resume(db, profile.active_resume_variant)
    return ProfileData(
        linkedin_url=profile.linkedin_url,
        active_resume_variant=profile.active_resume_variant,
        active_resume_label=active_resume.label if active_resume else None,
        active_resume_content=active_resume.content if active_resume else None,
    )


@router.post("/")
async def save_profile(data: ProfileUpdate, db: AsyncSession = Depends(get_db)):
    profile = await _get_profile(db)
    if not profile:
        profile = Profile(linkedin_url=data.linkedin_url, active_resume_variant=data.active_resume_variant)
        db.add(profile)
    else:
        profile.linkedin_url = data.linkedin_url
        profile.active_resume_variant = data.active_resume_variant
    await db.flush()
    return {"linkedin_url": profile.linkedin_url, "active_resume_variant": profile.active_resume_variant}


@router.post("/resume/file")
async def upload_resume_file(
    variant: str = Form("fdl"),
    label: str = Form("Uploaded resume"),
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    content = await _parse_resume_file(file)
    if not content.strip():
        raise HTTPException(status_code=400, detail="Uploaded file contains no text")

    profile = await _get_profile(db)
    if not profile:
        profile = Profile(linkedin_url="", active_resume_variant=variant)
        db.add(profile)

    r = await db.execute(
        select(Resume).where(Resume.variant == variant).order_by(Resume.version.desc())
    )
    latest = r.scalar_one_or_none()
    new_version = (latest.version + 1) if latest else 1
    if latest and latest.is_active:
        latest.is_active = False

    resume = Resume(
        variant=variant,
        version=new_version,
        label=label,
        content=content,
        is_active=True,
    )
    db.add(resume)
    profile.active_resume_variant = variant
    await db.flush()
    await db.refresh(resume)

    return {
        "id": resume.id,
        "variant": resume.variant,
        "version": resume.version,
        "label": resume.label,
        "content": resume.content,
        "is_active": resume.is_active,
    }


@router.post("/resume")
async def upload_resume(data: ResumeUpload, db: AsyncSession = Depends(get_db)):
    profile = await _get_profile(db)
    if not profile:
        profile = Profile(linkedin_url="", active_resume_variant=data.variant)
        db.add(profile)

    r = await db.execute(
        select(Resume).where(Resume.variant == data.variant).order_by(Resume.version.desc())
    )
    latest = r.scalar_one_or_none()
    new_version = (latest.version + 1) if latest else 1
    if latest and latest.is_active:
        latest.is_active = False

    resume = Resume(
        variant=data.variant,
        version=new_version,
        label=data.label,
        content=data.content,
        is_active=True,
    )
    db.add(resume)
    profile.active_resume_variant = data.variant
    await db.flush()
    await db.refresh(resume)

    return {
        "id": resume.id,
        "variant": resume.variant,
        "version": resume.version,
        "label": resume.label,
        "content": resume.content,
        "is_active": resume.is_active,
    }
