"""Events API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.models.content import (
    EventAssetImpact,
    EventEvidenceLink,
    EventLedger,
    RawDocument,
)
from backend.schemas.events import (
    EventAssetImpactRead,
    EventDetailRead,
    EventEvidenceLinkRead,
    EventLedgerList,
    EventLedgerRead,
    RawDocumentRead,
)

router = APIRouter(tags=["events"])


@router.get("/events", response_model=EventLedgerList)
async def list_events(
    instrument_id: UUID | None = Query(default=None),
    event_type: str | None = Query(default=None),
    verification_status: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> EventLedgerList:
    stmt = select(EventLedger)
    count_stmt = select(func.count()).select_from(EventLedger)

    if instrument_id:
        stmt = stmt.where(EventLedger.issuer_instrument_id == instrument_id)
        count_stmt = count_stmt.where(EventLedger.issuer_instrument_id == instrument_id)
    if event_type:
        stmt = stmt.where(EventLedger.event_type == event_type)
        count_stmt = count_stmt.where(EventLedger.event_type == event_type)
    if verification_status:
        stmt = stmt.where(EventLedger.verification_status == verification_status)
        count_stmt = count_stmt.where(EventLedger.verification_status == verification_status)

    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(
        stmt.offset(offset).limit(limit).order_by(EventLedger.created_at.desc())
    )
    items = [EventLedgerRead.model_validate(r) for r in result.scalars().all()]
    return EventLedgerList(items=items, total=total, limit=limit, offset=offset)


@router.get("/events/{event_id}", response_model=EventDetailRead)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> EventDetailRead:
    result = await db.execute(
        select(EventLedger).where(EventLedger.event_id == event_id)
    )
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    impacts_result = await db.execute(
        select(EventAssetImpact).where(EventAssetImpact.event_id == event_id)
    )
    evidence_result = await db.execute(
        select(EventEvidenceLink).where(EventEvidenceLink.event_id == event_id)
    )
    doc_result = await db.execute(
        select(RawDocument).where(RawDocument.raw_document_id == event.raw_document_id)
    )

    impacts = [
        EventAssetImpactRead.model_validate(i) for i in impacts_result.scalars().all()
    ]
    evidence = [
        EventEvidenceLinkRead.model_validate(e) for e in evidence_result.scalars().all()
    ]
    doc = doc_result.scalar_one_or_none()
    return EventDetailRead(
        event=EventLedgerRead.model_validate(event),
        asset_impacts=impacts,
        evidence_links=evidence,
        raw_document=RawDocumentRead.model_validate(doc) if doc else None,
    )
