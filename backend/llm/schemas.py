from pydantic import BaseModel
from typing import Optional
from enum import Enum


class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Role(str, Enum):
    GENERATOR = "generator"
    JUDGE = "judge"


class JudgeVerdict(str, Enum):
    PASS = "PASS"
    CHALLENGE = "CHALLENGE"
    FAIL = "FAIL"


class JudgeResult(BaseModel):
    verdict: JudgeVerdict
    score: float
    feedback: str
    specific_issues: list[str] = []
    improvement_suggestions: list[str] = []
    improved_content: Optional[str] = None
    model: str = ""
    quality: str = "full"  # "full" | "degraded" (when same-host judge)


class LLMResponse(BaseModel):
    content: str | dict | list
    generator_model: str
    complexity: Complexity
    generation_ms: int
    judge: Optional[JudgeResult] = None
    model_chain: list[str] = []
    cached: bool = False
