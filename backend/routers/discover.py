from fastapi import APIRouter
from pydantic import BaseModel
from llm.orchestrator import run

router = APIRouter()


class SuggestRequest(BaseModel):
    role_type: str = "Both"


PROFILE = (
    "Principal-level tech professional, 13+ years. GenAI/LLM deployment, enterprise solution architecture, "
    "customer-facing delivery, team leadership up to 50 engineers. Deployed: GenAI contractual drafting, "
    "multilingual AI platform 22 languages, RAG-based tax automation. UK-based, wants remote. "
    "IBM/Conduent/Accenture/Research QX/Sonnedix. 3 US patents. Davos World AI Forum 2025 keynote. "
    "Target: Principal/Lead TPM or Forward Deployment Lead."
)


@router.post("/suggest")
async def suggest(req: SuggestRequest):
    response = await run(
        task="discover.suggest",
        system="You are a career strategist with deep knowledge of the AI/enterprise tech hiring market.",
        prompt=f"Based on this profile, suggest 6 companies hiring for {req.role_type} roles in UK/remote AI/enterprise tech.\n\nPROFILE: {PROFILE}\n\nReturn JSON array: [{{\"company\":\"\",\"role_type\":\"\",\"location\":\"\",\"why_fit\":\"\",\"careers_url\":\"\"}}]",
        parse_json=True,
    )
    return {"suggestions": response.content, "meta": {"model_chain": response.model_chain, "generation_ms": response.generation_ms, "cached": response.cached}}
