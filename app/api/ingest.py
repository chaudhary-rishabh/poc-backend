import logging
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.session import Session
from app.schemas.ingest import IngestResponse
from app.services.doc_generation import generate_session_title
from app.services.ingestion import build_combined_text
from app.services.llm.factory import get_provider

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    files: list[UploadFile] = File(default=[]),
    text: str | None = Form(default=None),
    session_id: uuid.UUID | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    new_text = await build_combined_text(files, text)

    if session_id is None:
        session = Session(combined_text=new_text)
        db.add(session)
    else:
        session = await db.get(Session, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        session.combined_text = f"{session.combined_text}\n\n{new_text}" if session.combined_text else new_text

    if session.name is None and session.combined_text:
        try:
            provider = get_provider(None)
            session.name = await generate_session_title(provider, session.combined_text)
        except Exception:
            logger.exception("Session title generation failed for session %s", session.id)

    await db.commit()
    await db.refresh(session)

    return IngestResponse(session_id=session.id, combined_text=session.combined_text or "", name=session.name)
