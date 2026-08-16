from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.session import Session
from app.schemas.session import ApproveDocARequest, DocAResponse, ProviderRequest
from app.services.doc_generation import generate_doc_a
from app.services.llm.base import LLMGenerationError
from app.services.llm.factory import get_provider

router = APIRouter()


@router.post("/discovery", response_model=DocAResponse)
async def discovery(payload: ProviderRequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(Session, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.doc_a_status == "locked":
        raise HTTPException(
            status_code=400,
            detail="Doc A is locked. Use /approve/doc-a with action=regenerate to create a new draft.",
        )
    if not session.combined_text:
        raise HTTPException(status_code=400, detail="Session has no ingested content to analyze.")

    provider = get_provider(payload.provider)
    try:
        doc_a = await generate_doc_a(provider, session.combined_text)
    except LLMGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    session.doc_a = doc_a.model_dump()
    session.doc_a_status = "draft"
    session.provider = payload.provider or session.provider
    await db.commit()
    await db.refresh(session)

    return DocAResponse(session_id=session.id, doc_a=doc_a, doc_a_status="draft")


@router.post("/approve/doc-a", response_model=DocAResponse)
async def approve_doc_a(payload: ApproveDocARequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(Session, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.doc_a is None:
        raise HTTPException(status_code=400, detail="No draft Doc A exists for this session yet.")

    if payload.action == "approve":
        if session.doc_a_status == "locked":
            raise HTTPException(status_code=400, detail="Doc A is already locked.")
        session.doc_a_status = "locked"
        await db.commit()
        await db.refresh(session)
        return DocAResponse(session_id=session.id, doc_a=session.doc_a, doc_a_status="locked")

    # action == "regenerate"
    if not session.combined_text:
        raise HTTPException(status_code=400, detail="Session has no ingested content to analyze.")

    provider = get_provider(payload.provider)
    try:
        doc_a = await generate_doc_a(provider, session.combined_text)
    except LLMGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    session.doc_a = doc_a.model_dump()
    session.doc_a_status = "draft"
    session.provider = payload.provider or session.provider
    await db.commit()
    await db.refresh(session)

    return DocAResponse(session_id=session.id, doc_a=doc_a, doc_a_status="draft")
