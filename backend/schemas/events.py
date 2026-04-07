"""Event and content schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from backend.schemas.common import OrmBase, PaginatedResponse


class RawDocumentRead(OrmBase):
    """Raw document response schema."""
    raw_document_id: UUID
    source_id: UUID
    headline: str | None = None
    url: str | None = None
    language_code: str | None = None
    source_tier: str
    published_at: datetime
    ingested_at: datetime
    content_hash: str
    visibility_scope: str
    metadata_json: dict[str, Any]


class EventLedgerRead(OrmBase):
    """Event ledger response schema."""
    event_id: UUID
    raw_document_id: UUID
    event_type: str
    issuer_instrument_id: UUID | None = None
    market_profile_id: UUID | None = None
    event_time: datetime | None = None
    direction_hint: str | None = None
    materiality: Decimal | None = None
    novelty: Decimal | None = None
    corroboration_count: int
    extraction_version: str
    schema_version: str
    verification_status: str
    event_json: dict[str, Any]
    created_at: datetime


class EventLedgerList(PaginatedResponse):
    """Paginated list of events."""
    items: list[EventLedgerRead]


class EventAssetImpactRead(OrmBase):
    """Event asset impact response schema."""
    event_asset_impact_id: UUID
    event_id: UUID
    instrument_id: UUID
    impact_role: str
    direction_hint: str | None = None
    confidence: Decimal


class EventEvidenceLinkRead(OrmBase):
    """Event evidence link response schema."""
    event_evidence_link_id: UUID
    event_id: UUID
    raw_document_id: UUID
    evidence_kind: str
    span_start: int | None = None
    span_end: int | None = None
    weight: Decimal


class EventDetailRead(OrmBase):
    """Full event detail with impacts and evidence."""
    event: EventLedgerRead
    asset_impacts: list[EventAssetImpactRead]
    evidence_links: list[EventEvidenceLinkRead]
    raw_document: RawDocumentRead | None = None
