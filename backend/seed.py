"""Seed resumes into the database on first run."""
from models import Resume

SEED_RESUMES = [
    {
        "variant": "tpm",
        "label": "Base TPM resume",
        "content": """SOURAV BHATTACHARYA — Principal Technical Product Manager | AI & Digital Transformation
+44 7898 371247 | sav.accharya@gmail.com | linkedin.com/in/bhattacharyasourav

SUMMARY: Principal-level TPM, 13+ years, AI product strategy concept to production. Renewable energy, fintech, enterprise SaaS. GenAI/LLM architecture. Roadmap ownership, cross-functional leadership 30+ engineers. 3 US patents, 3 publications. Davos World AI Forum 2025 keynote.

SKILLS: Roadmap Strategy, OKR Definition, PRD/Spec Writing, Stakeholder Alignment, Go-to-Market, GenAI/LLM (GPT-4o, Claude, Mistral), RAG, LangChain, Vector DBs, Azure/AWS/GCP, System Design, Enterprise Architecture, API Design (FastAPI/REST), Agile/Scrum, CI/CD, Azure DevOps, JIRA, Docker, Kubernetes

EXPERIENCE:
Digital Innovation Architect | Sonnedix (Renewable Energy IPP) | Jul 2025-Present
- Founded Digital Innovation Lab: governance, 5-engineer team, £100K+ portfolio budget
- Shipped production GenAI contractual notice drafting system (concept to internal product)
- Secured £60K commercial sponsorship for Regulatory Intelligence Platform
- Launched automated drone pilot with Engineering & Construction
- Enterprise Architecture advisor: capability mapping, vendor evaluations, roadmaps
- Primary technical decision-enabler for C-suite

Senior Technical PM AI & Platform | Research QX Invenics | Nov 2020-Jun 2025
- GenAI R&D tax automation: 40-60% reduction, self-reflective RAG 80-90% accuracy, LangChain GPT-4o
- ApnaAI 22 languages: 30-35 engineers, App Store, 500+ downloads, 10K+ chats month one
- Scaled org 5 to 50+; promoted from Technical Architect

Technology R&D Specialist | Accenture Labs | Dec 2019-Aug 2020
Senior Research Engineer | Conduent Labs (Xerox) | Jul 2017-Sep 2019
Senior Android Developer | Mphasis (JP Morgan) | Sep 2014-Mar 2017
Android Developer | IBM Research India | Nov 2012-Sep 2014

PATENTS: US 11651257 B2 | US 11004006 B2 | Enforcement Routing 2022
AWARDS: Davos 2025 Keynote | Practice Dev Champion 2023 | Innovator of Year 2021"""
    },
    {
        "variant": "fdl",
        "label": "Base FDL resume",
        "content": """SOURAV BHATTACHARYA — Principal Forward Deployment Lead | AI & Enterprise Technology
+44 7898 371247 | sav.accharya@gmail.com | linkedin.com/in/bhattacharyasourav

SUMMARY: Principal-level FDL, 13+ years, deep technical architecture + customer-facing enterprise delivery. Architect bespoke AI solutions, drive POC to production, build C-suite trust. IBM/Accenture/Conduent/Invenics/Sonnedix. 3 patents, 3 publications. Davos 2025 keynote.

SKILLS: Enterprise POC Delivery, Technical Demos, Solution Architecture, Customer Onboarding, Pre-Sales, LLM Integration (GPT-4o, Claude, Mistral), RAG, LangChain, Vector DBs, Azure/AWS/GCP, API Design, Flutter/Android, IoT, Edge Computing, C-Suite Presentations, Business Case Development, Cross-functional Leadership 30+ engineers

EXPERIENCE:
Digital Innovation Architect | Sonnedix (Renewable Energy IPP) | Jul 2025-Present
- Primary technical advisor for senior stakeholders
- Production GenAI contractual notice drafting: stakeholder discovery through POC MVP to launch
- Secured £60K commercial sponsorship via business case presentation
- Launched automated drone pilot (concept to funded POC)
- Founded Digital Innovation Lab: 5-engineer team, £100K+ budget
- Enterprise Architecture advisor across service lines

Senior Technical PM AI & Platform | Research QX Invenics | Nov 2020-Jun 2025
- ApnaAI customer discovery and delivery: 500+ downloads, 10K+ chats month one
- Led 30-35 engineers, hybrid cloud Azure AWS GCP, Flutter, LLMs (OpenAI, Mistral, Claude)
- Self-reflective RAG 80-90% accuracy vs baselines
- Scaled org 5 to 50+

Technology R&D Specialist | Accenture Labs | Dec 2019-Aug 2020
Senior Research Engineer | Conduent Labs (Xerox) | Jul 2017-Sep 2019
- Sales decks, product demos and POCs for enterprise clients, pre-sales
- IoT US automated tolling; AR app Tattva patented US 11004006 B2
Senior Android Developer | Mphasis | Sep 2014-Mar 2017
Android Developer | IBM Research India | Nov 2012-Sep 2014

PATENTS: US 11651257 B2 | US 11004006 B2 | Enforcement Routing 2022
AWARDS: Davos 2025 Keynote | Practice Dev Champion 2023 | Innovator of Year 2021"""
    }
]


async def seed_resumes(db):
    from sqlalchemy import select
    result = await db.execute(select(Resume))
    if result.scalars().first():
        return  # already seeded
    for data in SEED_RESUMES:
        db.add(Resume(**data))
    await db.commit()
