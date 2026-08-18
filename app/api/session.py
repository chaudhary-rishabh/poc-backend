import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.discovery import regenerate_doc_a
from app.api.docs import regenerate_doc_b, regenerate_doc_c
from app.api.poc import regenerate_poc
from app.core.db import get_db
from app.models.session import Session
from app.schemas.session import ChatRequest, SessionResponse, SessionSummary

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


@router.delete("/session/{session_id}", status_code=204)
async def delete_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    session = await db.get(Session, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return Response(status_code=204)


@router.post("/session/{session_id}/chat")
async def chat(session_id: uuid.UUID, payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Thin dispatcher for the frontend's main chat input: routes a free-text
    message to the appropriate doc/POC regeneration path based on target_doc,
    passing the message through as feedback."""
    session = await db.get(Session, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if payload.target_doc == "doc_a":
        if session.doc_a is None:
            raise HTTPException(status_code=400, detail="No draft Doc A exists for this session yet.")
        return await regenerate_doc_a(session, payload.provider, payload.message, db)

    if payload.target_doc == "doc_b":
        return await regenerate_doc_b(session, payload.provider, payload.message, db)

    if payload.target_doc == "doc_c":
        return await regenerate_doc_c(session, payload.provider, payload.message, db)

    # target_doc == "poc"
    return await regenerate_poc(session, payload.provider, payload.message, db)
