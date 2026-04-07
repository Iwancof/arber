"""SQLAlchemy ORM models for the human_ops schema.

Human Inquiry Orchestration / Question Ops tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


# ---------------------------------------------------------------
# 1. InquiryCase
# ---------------------------------------------------------------
class InquiryCase(Base):
    __tablename__ = "inquiry_case"
    __table_args__ = (
        UniqueConstraint(
            "market_profile_code",
            "inquiry_kind",
            "dedupe_key",
            "case_status",
            name="uq_inquiry_case_dedupe",
        ),
        CheckConstraint(
            "linked_entity_type IN ("
            "'event','decision','position',"
            "'source_candidate','postmortem',"
            "'watchlist_item','market_regime')",
            name="ck_inquiry_case_linked_entity_type",
        ),
        CheckConstraint(
            "inquiry_kind IN ("
            "'pretrade_decision',"
            "'position_reassessment',"
            "'novel_event_interpretation',"
            "'source_gap_investigation',"
            "'postmortem_labeling',"
            "'prompt_reformat_request',"
            "'market_regime_call',"
            "'watchlist_reprioritization')",
            name="ck_inquiry_case_inquiry_kind",
        ),
        CheckConstraint(
            "urgency_class IN ("
            "'low','normal','high','critical')",
            name="ck_inquiry_case_urgency_class",
        ),
        CheckConstraint(
            "case_status IN ("
            "'open','monitoring','resolved','canceled')",
            name="ck_inquiry_case_case_status",
        ),
        {"schema": "human_ops"},
    )

    inquiry_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    market_profile_code: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    linked_entity_type: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    linked_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    inquiry_kind: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    dedupe_key: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    title: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    benchmark_symbol: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    primary_symbol: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    horizon_code: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    priority_score: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),
        server_default=text("0"),
        nullable=False,
    )
    urgency_class: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    case_status: Mapped[str] = mapped_column(
        Text,
        server_default=text("'open'"),
        nullable=False,
    )
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_trace_id: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )

    # relationships
    signals: Mapped[list[InquirySignal]] = relationship(
        back_populates="inquiry_case",
    )
    tasks: Mapped[list[InquiryTask]] = relationship(
        back_populates="inquiry_case",
    )


# ---------------------------------------------------------------
# 2. InquirySignal
# ---------------------------------------------------------------
class InquirySignal(Base):
    __tablename__ = "inquiry_signal"
    __table_args__ = (
        CheckConstraint(
            "signal_type IN ("
            "'high_materiality_low_confidence',"
            "'macro_single_name_conflict',"
            "'novel_event_type',"
            "'source_gap_detected',"
            "'policy_blocked_need_context',"
            "'position_monitoring_reassessment',"
            "'postmortem_needs_human_label',"
            "'schema_invalid_repeated',"
            "'market_regime_shift',"
            "'manual_watchlist_item')",
            name="ck_inquiry_signal_signal_type",
        ),
        {"schema": "human_ops"},
    )

    inquiry_signal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    inquiry_case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "human_ops.inquiry_case.inquiry_case_id"
        ),
        nullable=True,
    )
    signal_type: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    signal_score: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),
        server_default=text("0"),
        nullable=False,
    )
    source_ref_type: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    source_ref_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    explanation_json: Mapped[dict] = mapped_column(
        JSONB,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )

    # relationships
    inquiry_case: Mapped[InquiryCase | None] = (
        relationship(back_populates="signals")
    )


# ---------------------------------------------------------------
# 3. InquiryTask
# ---------------------------------------------------------------
class InquiryTask(Base):
    __tablename__ = "inquiry_task"
    __table_args__ = (
        UniqueConstraint(
            "inquiry_case_id",
            "revision_no",
            name="uq_inquiry_task_case_revision",
        ),
        CheckConstraint(
            "task_status IN ("
            "'draft','visible','claimed',"
            "'awaiting_response','submitted','parsed',"
            "'accepted','rejected','expired',"
            "'superseded','canceled')",
            name="ck_inquiry_task_task_status",
        ),
        CheckConstraint(
            "sla_class IN ("
            "'slow','normal','fast','urgent')",
            name="ck_inquiry_task_sla_class",
        ),
        {"schema": "human_ops"},
    )

    inquiry_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    inquiry_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "human_ops.inquiry_case.inquiry_case_id"
        ),
        nullable=False,
    )
    revision_no: Mapped[int] = mapped_column(
        Integer, nullable=False,
    )
    prompt_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "forecasting.prompt_task.prompt_task_id"
        ),
        nullable=True,
    )
    task_status: Mapped[str] = mapped_column(
        Text,
        server_default=text("'draft'"),
        nullable=False,
    )
    priority_score: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),
        server_default=text("0"),
        nullable=False,
    )
    sla_class: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    deadline_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    claim_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    prompt_pack_hash: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    evidence_bundle_hash: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    question_title: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    question_text: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    required_schema_name: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    required_schema_version: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    bounded_evidence_json: Mapped[dict] = mapped_column(
        JSONB,
        server_default=text("'[]'::jsonb"),
        nullable=False,
    )
    acceptance_rules_json: Mapped[dict] = mapped_column(
        JSONB,
        server_default=text("'[]'::jsonb"),
        nullable=False,
    )
    supersedes_inquiry_task_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "human_ops.inquiry_task.inquiry_task_id"
        ),
        nullable=True,
    )
    primary_response_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "human_ops.inquiry_response"
            ".inquiry_response_id"
        ),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.app_user.user_id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # relationships
    inquiry_case: Mapped[InquiryCase] = relationship(
        back_populates="tasks",
    )
    assignments: Mapped[list[InquiryAssignment]] = (
        relationship(back_populates="inquiry_task")
    )
    responses: Mapped[list[InquiryResponse]] = (
        relationship(
            back_populates="inquiry_task",
            foreign_keys=(
                "InquiryResponse.inquiry_task_id"
            ),
        )
    )
    resolutions: Mapped[list[InquiryResolution]] = (
        relationship(back_populates="inquiry_task")
    )
    superseded_task: Mapped[
        InquiryTask | None
    ] = relationship(
        "InquiryTask",
        remote_side="InquiryTask.inquiry_task_id",
        foreign_keys=[supersedes_inquiry_task_id],
    )


# ---------------------------------------------------------------
# 4. InquiryAssignment
# ---------------------------------------------------------------
class InquiryAssignment(Base):
    __tablename__ = "inquiry_assignment"
    __table_args__ = (
        CheckConstraint(
            "assignment_mode IN ('shared','exclusive')",
            name="ck_inquiry_assignment_mode",
        ),
        CheckConstraint(
            "assignment_status IN ("
            "'assigned','claimed','released',"
            "'expired','completed')",
            name="ck_inquiry_assignment_status",
        ),
        {"schema": "human_ops"},
    )

    inquiry_assignment_id: Mapped[uuid.UUID] = (
        mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=text("gen_random_uuid()"),
        )
    )
    inquiry_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "human_ops.inquiry_task.inquiry_task_id"
        ),
        nullable=False,
    )
    assigned_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.app_user.user_id"),
        nullable=True,
    )
    assignment_mode: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    assignment_status: Mapped[str] = mapped_column(
        Text,
        server_default=text("'assigned'"),
        nullable=False,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    claim_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )

    # relationships
    inquiry_task: Mapped[InquiryTask] = relationship(
        back_populates="assignments",
    )


# ---------------------------------------------------------------
# 5. InquiryPresence
# ---------------------------------------------------------------
class InquiryPresence(Base):
    __tablename__ = "inquiry_presence"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            name="uq_inquiry_presence_user",
        ),
        CheckConstraint(
            "availability_state IN ("
            "'online','busy','away','off_shift')",
            name="ck_inquiry_presence_availability",
        ),
        CheckConstraint(
            "focus_mode IN ("
            "'none','review','trading','postmortem')",
            name="ck_inquiry_presence_focus_mode",
        ),
        {"schema": "human_ops"},
    )

    inquiry_presence_id: Mapped[uuid.UUID] = (
        mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=text("gen_random_uuid()"),
        )
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.app_user.user_id"),
        nullable=False,
    )
    availability_state: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    focus_mode: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    can_receive_push: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("true"),
        nullable=False,
    )
    can_receive_urgent: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("true"),
        nullable=False,
    )
    timezone_name: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    working_hours_json: Mapped[dict] = mapped_column(
        JSONB,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------
# 6. InquiryResponse
# ---------------------------------------------------------------
class InquiryResponse(Base):
    __tablename__ = "inquiry_response"
    __table_args__ = (
        CheckConstraint(
            "response_channel IN ("
            "'direct_answer','external_llm',"
            "'api_import')",
            name="ck_inquiry_response_channel",
        ),
        CheckConstraint(
            "response_status IN ("
            "'received','parsed','valid','invalid',"
            "'accepted','rejected','late')",
            name="ck_inquiry_response_status",
        ),
        {"schema": "human_ops"},
    )

    inquiry_response_id: Mapped[uuid.UUID] = (
        mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=text("gen_random_uuid()"),
        )
    )
    inquiry_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "human_ops.inquiry_task.inquiry_task_id"
        ),
        nullable=False,
    )
    submitted_by: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.app_user.user_id"),
        nullable=True,
    )
    response_channel: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    model_name_user_entered: Mapped[
        str | None
    ] = mapped_column(
        Text, nullable=True,
    )
    response_status: Mapped[str] = mapped_column(
        Text,
        server_default=text("'received'"),
        nullable=False,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    raw_response: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    parsed_json: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
    )
    schema_valid: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        nullable=False,
    )
    parser_version: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    evidence_refs_json: Mapped[dict] = mapped_column(
        JSONB,
        server_default=text("'[]'::jsonb"),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )

    # relationships
    inquiry_task: Mapped[InquiryTask] = relationship(
        back_populates="responses",
        foreign_keys=[inquiry_task_id],
    )


# ---------------------------------------------------------------
# 7. InquiryResolution
# ---------------------------------------------------------------
class InquiryResolution(Base):
    __tablename__ = "inquiry_resolution"
    __table_args__ = (
        CheckConstraint(
            "resolution_status IN ("
            "'accepted','rejected','partial',"
            "'late_ignored','stale','superseded')",
            name="ck_inquiry_resolution_status",
        ),
        {"schema": "human_ops"},
    )

    inquiry_resolution_id: Mapped[uuid.UUID] = (
        mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=text("gen_random_uuid()"),
        )
    )
    inquiry_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "human_ops.inquiry_task.inquiry_task_id"
        ),
        nullable=False,
    )
    inquiry_response_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "human_ops.inquiry_response"
            ".inquiry_response_id"
        ),
        nullable=True,
    )
    resolution_status: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    effective_weight: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(10, 6), nullable=True,
    )
    used_for_decision: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        nullable=False,
    )
    affects_decision_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "forecasting.decision_ledger.decision_id"
        ),
        nullable=True,
    )
    resolution_reason_codes: Mapped[dict] = (
        mapped_column(
            JSONB,
            server_default=text("'[]'::jsonb"),
            nullable=False,
        )
    )
    resolved_by: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.app_user.user_id"),
        nullable=True,
    )
    resolved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )

    # relationships
    inquiry_task: Mapped[InquiryTask] = relationship(
        back_populates="resolutions",
    )


# ---------------------------------------------------------------
# 8. InquiryMetricSnapshot
# ---------------------------------------------------------------
class InquiryMetricSnapshot(Base):
    __tablename__ = "inquiry_metric_snapshot"
    __table_args__ = {"schema": "human_ops"}

    inquiry_metric_snapshot_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    open_count: Mapped[int] = mapped_column(
        Integer,
        server_default=text("0"),
        nullable=False,
    )
    due_soon_count: Mapped[int] = mapped_column(
        Integer,
        server_default=text("0"),
        nullable=False,
    )
    overdue_count: Mapped[int] = mapped_column(
        Integer,
        server_default=text("0"),
        nullable=False,
    )
    supersede_rate: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(10, 6), nullable=True,
    )
    response_latency_p50_sec: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(12, 3), nullable=True,
    )
    response_latency_p95_sec: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(12, 3), nullable=True,
    )
    accept_rate: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(10, 6), nullable=True,
    )
    late_response_rate: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(10, 6), nullable=True,
    )
    manual_uplift_score_delta: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(10, 6), nullable=True,
    )
    details_json: Mapped[dict] = mapped_column(
        JSONB,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
