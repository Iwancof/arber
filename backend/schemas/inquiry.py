"""Pydantic schemas for Human Inquiry Orchestration.

Covers: InquiryCase, InquiryTask, InquiryResponse,
InquiryResolution, InquiryPresence, metrics, and
the tray-item projection.
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


# ---------------------------------------------------------------
# InquiryCase
# ---------------------------------------------------------------
class InquiryCaseRead(OrmBase):
    """Read schema for an inquiry case."""

    inquiry_case_id: UUID
    market_profile_code: str
    linked_entity_type: str
    linked_entity_id: UUID | None = None
    inquiry_kind: str
    dedupe_key: str
    title: str
    benchmark_symbol: str | None = None
    primary_symbol: str | None = None
    horizon_code: str | None = None
    priority_score: Decimal
    urgency_class: str
    case_status: str
    opened_at: datetime
    updated_at: datetime
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
    )


class InquiryCaseCreate(OrmBase):
    """Create schema for an inquiry case."""

    market_profile_code: str
    linked_entity_type: str
    linked_entity_id: UUID | None = None
    inquiry_kind: str
    dedupe_key: str
    title: str
    benchmark_symbol: str | None = None
    primary_symbol: str | None = None
    horizon_code: str | None = None
    urgency_class: str = "normal"
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
    )


class InquiryCaseList(PaginatedResponse):
    """Paginated list of inquiry cases."""

    items: list[InquiryCaseRead]


# ---------------------------------------------------------------
# InquiryTask
# ---------------------------------------------------------------
class InquiryTaskRead(OrmBase):
    """Read schema for an inquiry task."""

    inquiry_task_id: UUID
    inquiry_case_id: UUID
    revision_no: int
    prompt_task_id: UUID | None = None
    task_status: str
    priority_score: Decimal
    sla_class: str
    deadline_at: datetime
    claim_expires_at: datetime | None = None
    prompt_pack_hash: str | None = None
    evidence_bundle_hash: str | None = None
    question_title: str
    question_text: str
    required_schema_name: str
    required_schema_version: str
    bounded_evidence_json: list[Any] = Field(
        default_factory=list,
    )
    acceptance_rules_json: list[str] = Field(
        default_factory=list,
    )
    supersedes_inquiry_task_id: (
        UUID | None
    ) = None
    primary_response_id: UUID | None = None
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime


class InquiryTaskList(PaginatedResponse):
    """Paginated list of inquiry tasks."""

    items: list[InquiryTaskRead]


# ---------------------------------------------------------------
# SpawnTask request body
# ---------------------------------------------------------------
class InquirySpawnTaskRequest(OrmBase):
    """Body for POST spawn-task."""

    question_title: str
    question_text: str
    deadline_at: datetime
    sla_class: str = "normal"
    bounded_evidence_json: list[Any] = Field(
        default_factory=list,
    )
    acceptance_rules_json: list[str] = Field(
        default_factory=list,
    )
    required_schema_name: str = "inquiry_response"
    required_schema_version: str = "1.0.0"


# ---------------------------------------------------------------
# InquiryTrayItem  (projection for the tray view)
# ---------------------------------------------------------------
class InquiryTrayItem(OrmBase):
    """Lightweight item shown in the question tray."""

    task_id: UUID
    case_id: UUID
    inquiry_kind: str
    market_profile_code: str
    primary_symbol: str | None = None
    task_status: str
    priority_score: Decimal
    sla_class: str
    deadline_at: datetime
    question_title: str
    time_bucket: str = "normal"


# ---------------------------------------------------------------
# InquiryResponse
# ---------------------------------------------------------------
class InquiryResponseCreate(OrmBase):
    """Body for submitting a response."""

    response_channel: str
    model_name_user_entered: str | None = None
    raw_response: str
    notes: str | None = None


class InquiryResponseRead(OrmBase):
    """Read schema for an inquiry response."""

    inquiry_response_id: UUID
    inquiry_task_id: UUID
    submitted_by: UUID | None = None
    response_channel: str
    model_name_user_entered: str | None = None
    response_status: str
    submitted_at: datetime
    raw_response: str
    parsed_json: dict[str, Any] | None = None
    schema_valid: bool
    parser_version: str | None = None
    evidence_refs_json: list[Any] = Field(
        default_factory=list,
    )
    notes: str | None = None


# ---------------------------------------------------------------
# InquiryResolution
# ---------------------------------------------------------------
class InquiryResolutionRead(OrmBase):
    """Read schema for an inquiry resolution."""

    inquiry_resolution_id: UUID
    inquiry_task_id: UUID
    inquiry_response_id: UUID | None = None
    resolution_status: str
    effective_weight: Decimal | None = None
    used_for_decision: bool
    affects_decision_id: UUID | None = None
    resolution_reason_codes: list[str] = Field(
        default_factory=list,
    )
    resolved_by: UUID | None = None
    resolved_at: datetime
    notes: str | None = None


# ---------------------------------------------------------------
# InquiryPresence
# ---------------------------------------------------------------
class InquiryPresenceUpdate(OrmBase):
    """Body for updating operator presence."""

    availability_state: str
    focus_mode: str
    can_receive_push: bool = True
    can_receive_urgent: bool = True


class InquiryPresenceRead(OrmBase):
    """Read schema for operator presence."""

    inquiry_presence_id: UUID
    user_id: UUID
    availability_state: str
    focus_mode: str
    can_receive_push: bool
    can_receive_urgent: bool
    updated_at: datetime


# ---------------------------------------------------------------
# Accept / Reject request bodies
# ---------------------------------------------------------------
class InquiryAcceptRequest(OrmBase):
    """Body for accepting a response."""

    response_id: UUID
    effective_weight: Decimal = Decimal("1.0")


class InquiryRejectRequest(OrmBase):
    """Body for rejecting a response."""

    response_id: UUID
    reason: str | None = None


# ---------------------------------------------------------------
# Snooze
# ---------------------------------------------------------------
class InquirySnoozeRequest(OrmBase):
    """Body for snoozing a task."""

    snooze_until: datetime


# ---------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------
class InquiryMetricsRead(OrmBase):
    """Aggregated inquiry metrics."""

    open_count: int = 0
    due_soon_count: int = 0
    overdue_count: int = 0
    supersede_rate: Decimal | None = None
    response_latency_p50_sec: (
        Decimal | None
    ) = None
    response_latency_p95_sec: (
        Decimal | None
    ) = None
    accept_rate: Decimal | None = None
    late_response_rate: Decimal | None = None
    manual_uplift_score_delta: (
        Decimal | None
    ) = None
