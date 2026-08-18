import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.doc_a import DocA
from app.schemas.doc_b import DocB
from app.schemas.doc_c import DocC

Provider = Literal["anthropic", "deepseek"]
Effort = Literal["low", "medium", "high"]


class ProviderRequest(BaseModel):
    session_id: uuid.UUID
    provider: Provider | None = None
    feedback: str | None = None
    model: str | None = None
    effort: Effort | None = None


class ApproveDocARequest(BaseModel):
    session_id: uuid.UUID
    action: Literal["approve", "regenerate"]
    provider: Provider | None = None
    feedback: str | None = None
    model: str | None = None
    effort: Effort | None = None


class ChatRequest(BaseModel):
    message: str
    target_doc: Literal["doc_a", "doc_b", "doc_c", "poc"]
    provider: Provider | None = None
    model: str | None = None
    effort: Effort | None = None


class RenameSessionRequest(BaseModel):
    name: str


class DocAResponse(BaseModel):
    session_id: uuid.UUID
    doc_a: DocA
    doc_a_status: Literal["draft", "locked"]


class DocBResponse(BaseModel):
    session_id: uuid.UUID
    doc_b: DocB
    stale_downstream: list[str] = []


class DocCResponse(BaseModel):
    session_id: uuid.UUID
    doc_c: DocC
    stale_downstream: list[str] = []


class PocResponse(BaseModel):
    html: str


class SessionResponse(BaseModel):
    id: uuid.UUID
    name: str | None
    combined_text: str | None
    provider: str | None
    model: str | None
    effort: str | None
    doc_a: DocA | None
    doc_a_status: str | None
    doc_b: DocB | None
    doc_c: DocC | None
    poc_html: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionSummary(BaseModel):
    id: uuid.UUID
    name: str | None
    created_at: datetime
    doc_a_status: str | None
    has_doc_b: bool
    has_doc_c: bool
    has_poc: bool

    model_config = {"from_attributes": True}
