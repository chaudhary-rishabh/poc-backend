from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.session import Session
from app.schemas.session import DocBResponse, DocCResponse, ProviderRequest
from app.services.doc_generation import generate_doc_b, generate_doc_c
from app.services.llm.base import LLMGenerationError
from app.services.llm.factory import get_provider

router = APIRouter()


async def regenerate_doc_b(
    session: Session, provider_name: str | None, feedback: str | None, db: AsyncSession
) -> DocBResponse:
    """Shared regeneration path for Doc B, used by /generate/doc-b and the
    /session/{id}/chat dispatcher."""
    if session.doc_a_status != "locked":
        raise HTTPException(status_code=400, detail="Doc A must be locked before generating Doc B.")

    provider = get_provider(provider_name)
    try:
        doc_b = await generate_doc_b(provider, session, feedback)
    except LLMGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    stale_downstream = []
    if session.doc_c is not None:
        stale_downstream.append("doc_c")
    if session.poc_html is not None:
        stale_downstream.append("poc")

    session.doc_b = doc_b.model_dump()
    session.provider = provider_name or session.provider
    await db.commit()
    await db.refresh(session)

    return DocBResponse(session_id=session.id, doc_b=doc_b, stale_downstream=stale_downstream)


async def regenerate_doc_c(
    session: Session, provider_name: str | None, feedback: str | None, db: AsyncSession
) -> DocCResponse:
    """Shared regeneration path for Doc C, used by /generate/doc-c and the
    /session/{id}/chat dispatcher."""
    if session.doc_b is None:
        raise HTTPException(status_code=400, detail="Doc B must be generated before generating Doc C.")

    provider = get_provider(provider_name)
    try:
        doc_c = await generate_doc_c(provider, session, feedback)
    except LLMGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    stale_downstream = []
    if session.poc_html is not None:
        stale_downstream.append("poc")

    session.doc_c = doc_c.model_dump()
    session.provider = provider_name or session.provider
    await db.commit()
    await db.refresh(session)

    return DocCResponse(session_id=session.id, doc_c=doc_c, stale_downstream=stale_downstream)


@router.post("/generate/doc-b", response_model=DocBResponse)
async def generate_doc_b_route(payload: ProviderRequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(Session, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return await regenerate_doc_b(session, payload.provider, payload.feedback, db)


@router.post("/generate/doc-c", response_model=DocCResponse)
async def generate_doc_c_route(payload: ProviderRequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(Session, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return await regenerate_doc_c(session, payload.provider, payload.feedback, db)
