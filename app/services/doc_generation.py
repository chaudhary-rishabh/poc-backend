import json

from pydantic import BaseModel, ValidationError

from app.models.session import Session
from app.schemas.doc_a import DocA
from app.schemas.doc_b import DocB
from app.schemas.doc_c import DocC
from app.services.llm.base import LLMGenerationError, LLMProvider
from app.services.prompts import (
    DOC_A_SYSTEM_PROMPT,
    DOC_B_SYSTEM_PROMPT,
    DOC_C_SYSTEM_PROMPT,
    build_retry_suffix,
)


async def generate_and_validate(
    system_prompt: str,
    user_content: str,
    response_model: type[BaseModel],
    provider: LLMProvider,
) -> BaseModel:
    """Shared call+validate+retry-once path for every doc generation stage.

    Calls the provider, validates the raw response against response_model. On
    ValidationError (or invalid JSON), retries exactly once with the error
    appended via build_retry_suffix(). If the retry also fails, raises
    LLMGenerationError — the route layer turns that into a 502.
    """
    raw = await provider.complete(system_prompt, user_content)

    try:
        return response_model.model_validate(_parse_json(raw))
    except (ValidationError, json.JSONDecodeError) as e:
        retry_content = user_content + build_retry_suffix(str(e))
        raw_retry = await provider.complete(system_prompt, retry_content)
        try:
            return response_model.model_validate(_parse_json(raw_retry))
        except (ValidationError, json.JSONDecodeError) as e2:
            raise LLMGenerationError(f"Response failed validation after retry: {e2}") from e2


def _parse_json(raw: str):
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return json.loads(cleaned.strip())


async def generate_doc_a(provider: LLMProvider, combined_text: str) -> DocA:
    return await generate_and_validate(DOC_A_SYSTEM_PROMPT, combined_text, DocA, provider)


async def generate_doc_b(provider: LLMProvider, session: Session) -> DocB:
    user_content = json.dumps(session.doc_a)
    return await generate_and_validate(DOC_B_SYSTEM_PROMPT, user_content, DocB, provider)


async def generate_doc_c(provider: LLMProvider, session: Session) -> DocC:
    user_content = json.dumps({"doc_a": session.doc_a, "doc_b": session.doc_b})
    return await generate_and_validate(DOC_C_SYSTEM_PROMPT, user_content, DocC, provider)
