"""Source registry schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from backend.schemas.common import OrmBase, PaginatedResponse


class SourceRegistryRead(OrmBase):
    """Source registry response schema."""
    source_id: UUID
    source_code: str
    display_name: str
    source_type: str
    adapter_type: str
    trust_tier: str
    latency_class: str
    coverage_tags_json: list[Any]
    markets_json: list[Any]
    languages_json: list[Any]
    retention_days: int
    owner_team: str | None = None
    status: str
    created_at: datetime


class SourceRegistryCreate(OrmBase):
    """Source registry creation schema."""
    source_code: str
    display_name: str
    source_type: str
    adapter_type: str
    trust_tier: str
    latency_class: str
    coverage_tags_json: list[Any] = []
    markets_json: list[Any] = []
    languages_json: list[Any] = []
    retention_days: int = 365
    legal_notes: str | None = None
    owner_team: str | None = None


class SourceRegistryUpdate(OrmBase):
    """Source registry partial update schema."""
    display_name: str | None = None
    trust_tier: str | None = None
    coverage_tags_json: list[Any] | None = None
    markets_json: list[Any] | None = None
    status: str | None = None
    owner_team: str | None = None


class SourceRegistryList(PaginatedResponse):
    """Paginated list of sources."""
    items: list[SourceRegistryRead]


class SourceEndpointRead(OrmBase):
    """Source endpoint response schema."""
    source_endpoint_id: UUID
    source_id: UUID
    endpoint_name: str
    endpoint_url: str
    endpoint_type: str
    auth_profile: str | None = None
    polling_interval_sec: int | None = None
    rate_limit_per_minute: int | None = None
    active: bool
    metadata_json: dict[str, Any]


class SourceEndpointCreate(OrmBase):
    """Source endpoint creation schema."""
    source_id: UUID
    endpoint_name: str
    endpoint_url: str
    endpoint_type: str
    auth_profile: str | None = None
    polling_interval_sec: int | None = None
    rate_limit_per_minute: int | None = None
    metadata_json: dict[str, Any] = {}


class SourceBundleRead(OrmBase):
    """Source bundle response schema."""
    source_bundle_id: UUID
    bundle_code: str
    display_name: str
    market_profile_id: UUID | None = None
    bundle_scope: str
    applies_to_asset_class: str | None = None
    applies_to_sector: str | None = None
    active: bool
    metadata_json: dict[str, Any]


class SourceBundleCreate(OrmBase):
    """Source bundle creation schema."""
    bundle_code: str
    display_name: str
    market_profile_id: UUID | None = None
    bundle_scope: str
    applies_to_asset_class: str | None = None
    applies_to_sector: str | None = None
    metadata_json: dict[str, Any] = {}


class SourceCandidateRead(OrmBase):
    """Source candidate response schema."""
    source_candidate_id: UUID
    proposed_source_code: str
    display_name: str
    proposed_adapter_type: str
    proposal_type: str
    why_now: str
    expected_coverage_json: list[Any]
    linked_market_profile_id: UUID | None = None
    proposed_by_type: str
    proposed_by: str
    status: str
    review_notes: str | None = None
    created_at: datetime
    reviewed_at: datetime | None = None


class SourceCandidateList(PaginatedResponse):
    """Paginated list of source candidates."""
    items: list[SourceCandidateRead]
