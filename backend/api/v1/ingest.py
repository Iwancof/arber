"""Document ingestion API endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.schemas.events import RawDocumentRead
from backend.services.ingest import ingest_document

router = APIRouter(tags=["ingest"])


class IngestDocumentRequest(BaseModel):
    """Request body for document ingestion."""
    source_id: UUID
    headline: str | None = None
    url: str | None = None
    raw_text: str | None = None
    raw_payload_json: dict[str, Any] = {}
    published_at: datetime
    language_code: str | None = None
    source_tier: str = "medium_vendor"
    native_doc_id: str | None = None
    market_profile_hint_id: UUID | None = None
    visibility_scope: str = "internal"
    metadata_json: dict[str, Any] = {}


@router.post("/ingest/documents", response_model=RawDocumentRead, status_code=201)
async def ingest_doc(
    body: IngestDocumentRequest,
    db: AsyncSession = Depends(get_db),
) -> RawDocumentRead:
    """Ingest a raw document into the system."""
    doc = await ingest_document(db, **body.model_dump())
    return RawDocumentRead.model_validate(doc)
