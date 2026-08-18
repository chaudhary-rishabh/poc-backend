import uuid

from pydantic import BaseModel


class IngestResponse(BaseModel):
    session_id: uuid.UUID
    combined_text: str
    name: str | None = None
