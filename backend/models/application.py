from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(200), default="")
    role = Column(String(200), nullable=False)
    location = Column(String(200), default="")
    url = Column(Text, default="")
    status = Column(String(50), default="Saved", nullable=False)
    match_score = Column(Integer, nullable=True)
    resume_variant = Column(String(10), default="fdl", nullable=False)
    notes = Column(Text, default="")
    jd_text = Column(Text, default="")
    rewritten_resume = Column(Text, default="")
    rewritten_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
