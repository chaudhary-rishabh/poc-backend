import json

from app.models.session import Session
from app.schemas.doc_a import DocA
from app.schemas.doc_b import DocB
from app.schemas.doc_c import DocC
from app.services.llm.base import LLMProvider
from app.services.prompts import DOC_A_SYSTEM_PROMPT, DOC_B_SYSTEM_PROMPT, DOC_C_SYSTEM_PROMPT


async def generate_doc_a(provider: LLMProvider, combined_text: str) -> DocA:
    return await provider.generate_structured(DOC_A_SYSTEM_PROMPT, combined_text, DocA)


async def generate_doc_b(provider: LLMProvider, session: Session) -> DocB:
    user_content = json.dumps(session.doc_a)
    return await provider.generate_structured(DOC_B_SYSTEM_PROMPT, user_content, DocB)


async def generate_doc_c(provider: LLMProvider, session: Session) -> DocC:
    user_content = json.dumps({"doc_a": session.doc_a, "doc_b": session.doc_b})
    return await provider.generate_structured(DOC_C_SYSTEM_PROMPT, user_content, DocC)
