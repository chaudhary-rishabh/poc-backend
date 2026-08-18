from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.session import Session
from app.schemas.doc_b import DocB
from app.schemas.session import PocResponse, ProviderRequest
from app.services.llm.base import LLMGenerationError
from app.services.llm.factory import get_provider
from app.services.poc_builder import build_poc_html

router = APIRouter()


async def regenerate_poc(
    session: Session,
    provider_name: str | None,
    feedback: str | None,
    db: AsyncSession,
    model: str | None = None,
    effort: str | None = None,
) -> PocResponse:
    """Shared regeneration path for the POC, used by /generate/poc and the
    /session/{id}/chat dispatcher."""
    if session.doc_b is None:
        raise HTTPException(status_code=400, detail="Doc B must be generated before generating the POC.")

    doc_b = DocB.model_validate(session.doc_b)
    provider = get_provider(provider_name)
    current_poc_html = session.poc_html if feedback else None

    try:
        html = await build_poc_html(provider, doc_b, feedback, current_poc_html, model, effort)
    except LLMGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    session.poc_html = html
    session.provider = provider_name or session.provider
    session.model = model or session.model
    session.effort = effort or session.effort
    await db.commit()

    return PocResponse(html=html)


@router.post("/generate/poc", response_model=PocResponse)
async def generate_poc(payload: ProviderRequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(Session, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return await regenerate_poc(
        session, payload.provider, payload.feedback, db, payload.model, payload.effort
    )
