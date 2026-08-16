import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.session import Session
from app.schemas.session import SessionResponse, SessionSummary

router = APIRouter()


@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    columns = (
        Session.id,
        Session.name,
        Session.created_at,
        Session.doc_a_status,
        Session.doc_b,
        Session.doc_c,
        Session.poc_html,
    )
    result = await db.execute(select(*columns).order_by(Session.created_at.desc()))
    rows = result.all()

    return [
        SessionSummary(
            id=row.id,
            name=row.name,
            created_at=row.created_at,
            doc_a_status=row.doc_a_status,
            has_doc_b=row.doc_b is not None,
            has_doc_c=row.doc_c is not None,
            has_poc=row.poc_html is not None,
        )
        for row in rows
    ]


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    session = await db.get(Session, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
