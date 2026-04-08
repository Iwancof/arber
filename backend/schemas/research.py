"""Pydantic schemas for Research Scout.

Covers: ResearchCase, ResearchJob,
SymbolDossierSnapshot, CandidateSymbol,
ResearchBrief, and analog search results.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from backend.schemas.common import (
    OrmBase,
    PaginatedResponse,
)


# -----------------------------------------------------------
# ResearchCase
# -----------------------------------------------------------
class ResearchScopeCreate(OrmBase):
    """Scope item in case creation."""

    scope_type: str
    scope_key: str
    scope_role: str
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
    )


class ResearchCaseCreate(OrmBase):
    """Create schema for a research case."""

    case_type: str
    market_code: str
    primary_symbol: str | None = None
    benchmark_symbol: str | None = None
    title: str
    trigger_reason: str | None = None
    scopes: list[ResearchScopeCreate] = Field(
        default_factory=list,
    )


class ResearchScopeRead(OrmBase):
    """Read schema for a research scope."""

    scope_id: UUID
    case_id: UUID
    scope_type: str
    scope_key: str
    scope_role: str
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
    )
    created_at: datetime


class ResearchCaseRead(OrmBase):
    """Read schema for a research case."""

    case_id: UUID
    case_type: str
    market_code: str
    primary_symbol: str | None = None
    benchmark_symbol: str | None = None
    title: str
    status: str
    priority: int
    trigger_reason: str | None = None
    current_hypothesis_summary: (
        str | None
    ) = None
    current_question_summary: (
        str | None
    ) = None
    trace_id: str | None = None
    correlation_id: str | None = None
    created_at: datetime
    updated_at: datetime
    first_seen_at: datetime
    last_updated_at: datetime
    scopes: list[ResearchScopeRead] = Field(
        default_factory=list,
    )


class ResearchCaseList(PaginatedResponse):
    """Paginated list of research cases."""

    items: list[ResearchCaseRead]


# -----------------------------------------------------------
# ResearchJob
# -----------------------------------------------------------
class ResearchQueryPlanCreate(OrmBase):
    """Query plan item in job creation."""

    query_kind: str
    query_text: str
    max_docs: int = 20
    source_filter_json: dict[str, Any] = Field(
        default_factory=dict,
    )


class ResearchJobCreate(OrmBase):
    """Create schema for a research job."""

    case_id: UUID | None = None
    job_type: str
    trigger_type: str
    budget_class: str
    worker_adapter: str | None = None
    prompt_version: str | None = None
    query_plans: list[
        ResearchQueryPlanCreate
    ] = Field(default_factory=list)


class ResearchQueryPlanRead(OrmBase):
    """Read schema for a query plan."""

    plan_id: UUID
    job_id: UUID
    query_kind: str
    source_filter_json: dict[str, Any] = Field(
        default_factory=dict,
    )
    query_text: str
    time_window_start: datetime | None = None
    time_window_end: datetime | None = None
    max_docs: int
    status: str
    created_at: datetime


class ResearchJobRead(OrmBase):
    """Read schema for a research job."""

    job_id: UUID
    case_id: UUID | None = None
    job_type: str
    trigger_type: str
    budget_class: str
    status: str
    worker_adapter: str | None = None
    prompt_version: str | None = None
    input_hash: str | None = None
    result_summary: str | None = None
    trace_id: str | None = None
    correlation_id: str | None = None
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    next_run_at: datetime | None = None
    created_at: datetime
    query_plans: list[
        ResearchQueryPlanRead
    ] = Field(default_factory=list)


class ResearchJobList(PaginatedResponse):
    """Paginated list of research jobs."""

    items: list[ResearchJobRead]


# -----------------------------------------------------------
# SymbolDossier
# -----------------------------------------------------------
class SymbolDossierRead(OrmBase):
    """Read schema for a symbol dossier snapshot."""

    snapshot_id: UUID
    market_code: str
    symbol: str
    asof: datetime
    watch_status: str
    benchmark_symbol: str | None = None
    current_thesis: str | None = None
    payload_json: dict[str, Any] = Field(
        default_factory=dict,
    )
    quality_score: Decimal | None = None
    coverage_score: Decimal | None = None
    research_depth_score: (
        Decimal | None
    ) = None
    freshness_class: str
    source_case_id: UUID | None = None
    created_at: datetime


# -----------------------------------------------------------
# CandidateSymbol
# -----------------------------------------------------------
class CandidateSymbolRead(OrmBase):
    """Read schema for a candidate symbol."""

    candidate_id: UUID
    market_code: str
    symbol: str
    discovered_from_case_id: (
        UUID | None
    ) = None
    discovered_from_event_ref: (
        str | None
    ) = None
    relation_to_watchlist: str
    candidate_reason_codes: list[Any] = Field(
        default_factory=list,
    )
    discovery_score: Decimal
    promotion_score: Decimal | None = None
    status: str
    first_seen_at: datetime
    last_seen_at: datetime
    promoted_at: datetime | None = None
    rejected_at: datetime | None = None
    decision_note: str | None = None
    trace_id: str | None = None
    correlation_id: str | None = None
    created_at: datetime


class CandidateSymbolList(PaginatedResponse):
    """Paginated list of candidate symbols."""

    items: list[CandidateSymbolRead]


class PromoteCandidateRequest(OrmBase):
    """Body for promoting a candidate symbol."""

    promotion_level: str
    note: str | None = None


class RejectCandidateRequest(OrmBase):
    """Body for rejecting a candidate symbol."""

    reason: str | None = None


class SnoozeCandidateRequest(OrmBase):
    """Body for snoozing a candidate symbol."""

    until: datetime | None = None


# -----------------------------------------------------------
# ResearchAnalog (evidence-based analog)
# -----------------------------------------------------------
class ResearchAnalogRead(OrmBase):
    """Read schema for a historical analog."""

    evidence_id: UUID
    case_id: UUID
    source_type: str
    evidence_role: str
    symbol: str | None = None
    event_type: str | None = None
    published_at: datetime | None = None
    relevance_score: Decimal | None = None
    novelty_score: Decimal | None = None
    summary: str | None = None
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
    )
    created_at: datetime


# -----------------------------------------------------------
# ResearchBrief
# -----------------------------------------------------------
class ResearchBriefRead(OrmBase):
    """Read schema for a research brief."""

    brief_id: UUID
    case_id: UUID
    brief_kind: str
    version: int
    status: str
    brief_json: dict[str, Any] = Field(
        default_factory=dict,
    )
    expires_at: datetime | None = None
    trace_id: str | None = None
    created_at: datetime
