from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.session import Session
from app.schemas.doc_b import DocB
from app.schemas.session import PocResponse, ProviderRequest
from app.services.poc_builder import build_poc_html

router = APIRouter()


@router.post("/generate/poc", response_model=PocResponse)
async def generate_poc(payload: ProviderRequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(Session, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.doc_b is None:
        raise HTTPException(status_code=400, detail="Doc B must be generated before generating the POC.")

    doc_b = DocB.model_validate(session.doc_b)
    title = session.name or "POC Mockup"

    try:
        html = build_poc_html(doc_b, app_title=title)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    session.poc_html = html
    await db.commit()

    return PocResponse(html=html)
