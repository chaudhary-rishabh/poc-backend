import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.doc_a import DocA
from app.schemas.doc_b import DocB
from app.schemas.doc_c import DocC

Provider = Literal["anthropic", "deepseek"]


class ProviderRequest(BaseModel):
    session_id: uuid.UUID
    provider: Provider | None = None


class ApproveDocARequest(BaseModel):
    session_id: uuid.UUID
    action: Literal["approve", "regenerate"]
    provider: Provider | None = None


class DocAResponse(BaseModel):
    session_id: uuid.UUID
    doc_a: DocA
    doc_a_status: Literal["draft", "locked"]


class DocBResponse(BaseModel):
    session_id: uuid.UUID
    doc_b: DocB


class DocCResponse(BaseModel):
    session_id: uuid.UUID
    doc_c: DocC


class PocResponse(BaseModel):
    html: str


class SessionResponse(BaseModel):
    id: uuid.UUID
    name: str | None
    combined_text: str | None
    provider: str | None
    doc_a: DocA | None
    doc_a_status: str | None
    doc_b: DocB | None
    doc_c: DocC | None
    poc_html: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
