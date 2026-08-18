from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import discovery, docs, ingest, models, poc, session
from app.core.config import settings

app = FastAPI(title="AI Discovery Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, tags=["ingest"])
app.include_router(discovery.router, tags=["discovery"])
app.include_router(docs.router, tags=["docs"])
app.include_router(poc.router, tags=["poc"])
app.include_router(session.router, tags=["session"])
app.include_router(models.router, tags=["models"])


@app.get("/health")
async def health():
    return {"status": "ok"}
