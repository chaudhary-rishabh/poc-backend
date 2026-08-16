import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.session import Session
from app.schemas.ingest import IngestResponse
from app.services.ingestion import build_combined_text

router = APIRouter()


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

    await db.commit()
    await db.refresh(session)

    return IngestResponse(session_id=session.id, combined_text=session.combined_text or "")
