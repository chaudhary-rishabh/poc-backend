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
    SESSION_TITLE_SYSTEM_PROMPT,
    build_retry_suffix,
)


def _append_feedback(
    user_content: str, feedback: str | None, current_version: dict | None = None
) -> str:
    if not feedback:
        return user_content
    if current_version is not None:
        current_version_json = json.dumps(current_version)
        user_content += (
            f"\n\nCURRENT VERSION (this is the baseline to revise, not a fresh input to ignore):\n"
            f"{current_version_json}"
        )
    user_content += (
        f"\n\nUSER FEEDBACK (required correction — apply it directly to the current version above):\n"
        f"{feedback}"
    )
    return user_content


async def generate_and_validate(
    system_prompt: str,
    user_content: str,
    response_model: type[BaseModel],
    provider: LLMProvider,
    feedback: str | None = None,
    current_version: dict | None = None,
) -> BaseModel:
    """Shared call+validate+retry-once path for every doc generation stage.

    Calls the provider, validates the raw response against response_model. On
    ValidationError (or invalid JSON), retries exactly once with the error
    appended via build_retry_suffix(). If the retry also fails, raises
    LLMGenerationError — the route layer turns that into a 502.
    """
    user_content = _append_feedback(user_content, feedback, current_version)
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


async def generate_doc_a(
    provider: LLMProvider,
    combined_text: str,
    feedback: str | None = None,
    current_doc_a: dict | None = None,
) -> DocA:
    return await generate_and_validate(
        DOC_A_SYSTEM_PROMPT, combined_text, DocA, provider, feedback, current_doc_a
    )


async def generate_doc_b(provider: LLMProvider, session: Session, feedback: str | None = None) -> DocB:
    user_content = json.dumps(session.doc_a)
    current_doc_b = session.doc_b if feedback else None
    return await generate_and_validate(
        DOC_B_SYSTEM_PROMPT, user_content, DocB, provider, feedback, current_doc_b
    )


async def generate_doc_c(provider: LLMProvider, session: Session, feedback: str | None = None) -> DocC:
    user_content = json.dumps({"doc_a": session.doc_a, "doc_b": session.doc_b})
    current_doc_c = session.doc_c if feedback else None
    return await generate_and_validate(
        DOC_C_SYSTEM_PROMPT, user_content, DocC, provider, feedback, current_doc_c
    )


async def generate_session_title(provider: LLMProvider, combined_text: str) -> str:
    """Short auto-generated session name from the first bit of raw input —
    just enough signal to name the session, not the full text."""
    title = await provider.complete(SESSION_TITLE_SYSTEM_PROMPT, combined_text[:4000], max_tokens=30)
    return title.strip().strip('"').strip("'")[:80]
