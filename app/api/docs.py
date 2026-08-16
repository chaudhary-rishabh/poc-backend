from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.session import Session
from app.schemas.session import DocBResponse, DocCResponse, ProviderRequest
from app.services.doc_generation import generate_doc_b, generate_doc_c
from app.services.llm.base import LLMGenerationError
from app.services.llm.factory import get_provider

router = APIRouter()


@router.post("/generate/doc-b", response_model=DocBResponse)
async def generate_doc_b_route(payload: ProviderRequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(Session, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.doc_a_status != "locked":
        raise HTTPException(status_code=400, detail="Doc A must be locked before generating Doc B.")

    provider = get_provider(payload.provider)
    try:
        doc_b = await generate_doc_b(provider, session)
    except LLMGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    session.doc_b = doc_b.model_dump()
    session.provider = payload.provider or session.provider
    await db.commit()
    await db.refresh(session)

    return DocBResponse(session_id=session.id, doc_b=doc_b)


@router.post("/generate/doc-c", response_model=DocCResponse)
async def generate_doc_c_route(payload: ProviderRequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(Session, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.doc_b is None:
        raise HTTPException(status_code=400, detail="Doc B must be generated before generating Doc C.")

    provider = get_provider(payload.provider)
    try:
        doc_c = await generate_doc_c(provider, session)
    except LLMGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    session.doc_c = doc_c.model_dump()
    session.provider = payload.provider or session.provider
    await db.commit()
    await db.refresh(session)

    return DocCResponse(session_id=session.id, doc_c=doc_c)
