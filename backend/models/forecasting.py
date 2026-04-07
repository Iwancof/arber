"""SQLAlchemy ORM models for the `forecasting` schema."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.execution import OrderLedger

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


# ---------------------------------------------------------------------------
# 1. RetrievalSet
# ---------------------------------------------------------------------------
class RetrievalSet(Base):
    __tablename__ = "retrieval_set"
    __table_args__ = (
        CheckConstraint(
            "retrieval_mode IN ('episodic','semantic','mixed','manual')",
            name="ck_retrieval_set_retrieval_mode",
        ),
        {"schema": "forecasting"},
    )

    retrieval_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.event_ledger.event_id"),
        nullable=True,
    )
    retrieval_version: Mapped[str] = mapped_column(Text, nullable=False)
    retrieval_mode: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    # relationships
    items: Mapped[list[RetrievalItem]] = relationship(
        back_populates="retrieval_set", cascade="all, delete-orphan"
    )
    reasoning_traces: Mapped[list[ReasoningTrace]] = relationship(
        back_populates="retrieval_set"
    )


# ---------------------------------------------------------------------------
# 2. RetrievalItem
# ---------------------------------------------------------------------------
class RetrievalItem(Base):
    __tablename__ = "retrieval_item"
    __table_args__ = (
        CheckConstraint(
            "item_type IN ('raw_document','event','semantic_stat','case','market_snapshot')",
            name="ck_retrieval_item_item_type",
        ),
        {"schema": "forecasting"},
    )

    retrieval_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    retrieval_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forecasting.retrieval_set.retrieval_set_id"),
        nullable=False,
    )
    item_type: Mapped[str] = mapped_column(Text, nullable=False)
    item_ref_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    item_ref_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rank: Mapped[int] = mapped_column(
        SmallInteger, server_default=text("1"), nullable=False
    )
    similarity_score: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 6), nullable=True
    )
    selected_by: Mapped[str] = mapped_column(
        Text, server_default=text("'rule'"), nullable=False
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    # relationships
    retrieval_set: Mapped[RetrievalSet] = relationship(back_populates="items")


# ---------------------------------------------------------------------------
# 3. ReasoningTrace
# ---------------------------------------------------------------------------
class ReasoningTrace(Base):
    __tablename__ = "reasoning_trace"
    __table_args__ = ({"schema": "forecasting"},)

    reasoning_trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.event_ledger.event_id"),
        nullable=True,
    )
    retrieval_set_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forecasting.retrieval_set.retrieval_set_id"),
        nullable=True,
    )
    trace_version: Mapped[str] = mapped_column(Text, nullable=False)
    trace_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    retrieval_set: Mapped[RetrievalSet | None] = relationship(
        back_populates="reasoning_traces"
    )
    forecasts: Mapped[list[ForecastLedger]] = relationship(
        back_populates="reasoning_trace"
    )


# ---------------------------------------------------------------------------
# 4. ForecastLedger
# ---------------------------------------------------------------------------
class ForecastLedger(Base):
    __tablename__ = "forecast_ledger"
    __table_args__ = (
        CheckConstraint(
            "forecast_mode IN ('replay','shadow','paper','micro_live','live')",
            name="ck_forecast_ledger_forecast_mode",
        ),
        {"schema": "forecasting"},
    )

    forecast_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.event_ledger.event_id"),
        nullable=True,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.instrument.instrument_id"),
        nullable=False,
    )
    benchmark_instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.instrument.instrument_id"),
        nullable=True,
    )
    market_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.market_profile.market_profile_id"),
        nullable=False,
    )
    reasoning_trace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forecasting.reasoning_trace.reasoning_trace_id"),
        nullable=True,
    )
    model_family: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[str] = mapped_column(Text, nullable=False)
    worker_id: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_template_id: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[str] = mapped_column(Text, nullable=False)
    forecast_mode: Mapped[str] = mapped_column(Text, nullable=False)
    forecasted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    no_trade_reason_codes_json: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )
    forecast_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    # relationships
    reasoning_trace: Mapped[ReasoningTrace | None] = relationship(
        back_populates="forecasts"
    )
    horizons: Mapped[list[ForecastHorizon]] = relationship(
        back_populates="forecast", cascade="all, delete-orphan"
    )
    decisions: Mapped[list[DecisionLedger]] = relationship(
        back_populates="forecast"
    )


# ---------------------------------------------------------------------------
# 5. ForecastHorizon
# ---------------------------------------------------------------------------
class ForecastHorizon(Base):
    __tablename__ = "forecast_horizon"
    __table_args__ = (
        UniqueConstraint(
            "forecast_id", "horizon_code",
            name="uq_forecast_horizon_forecast_code",
        ),
        CheckConstraint(
            "horizon_code IN ('1d','5d','20d','1w','1m')",
            name="ck_forecast_horizon_horizon_code",
        ),
        {"schema": "forecasting"},
    )

    forecast_horizon_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    forecast_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forecasting.forecast_ledger.forecast_id"),
        nullable=False,
    )
    horizon_code: Mapped[str] = mapped_column(Text, nullable=False)
    p_outperform: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    p_underperform: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    p_downside_barrier: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    ret_q10: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 8), nullable=True
    )
    ret_q50: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 8), nullable=True
    )
    ret_q90: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 8), nullable=True
    )
    vol_forecast: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 8), nullable=True
    )

    # relationships
    forecast: Mapped[ForecastLedger] = relationship(back_populates="horizons")


# ---------------------------------------------------------------------------
# 6. DecisionLedger
# ---------------------------------------------------------------------------
class DecisionLedger(Base):
    __tablename__ = "decision_ledger"
    __table_args__ = (
        CheckConstraint(
            "execution_mode IN ('replay','shadow','paper','micro_live','live')",
            name="ck_decision_ledger_execution_mode",
        ),
        CheckConstraint(
            "action IN ('long_candidate','short_candidate','no_trade',"
            "'wait_manual','reduce','exit')",
            name="ck_decision_ledger_action",
        ),
        CheckConstraint(
            "decision_status IN ('candidate','waiting_manual','approved',"
            "'rejected','submitted_to_execution','suppressed','canceled')",
            name="ck_decision_ledger_decision_status",
        ),
        {"schema": "forecasting"},
    )

    decision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    forecast_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forecasting.forecast_ledger.forecast_id"),
        nullable=False,
    )
    market_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.market_profile.market_profile_id"),
        nullable=False,
    )
    execution_mode: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(8, 6), nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    decision_status: Mapped[str] = mapped_column(Text, nullable=False)
    policy_version: Mapped[str] = mapped_column(Text, nullable=False)
    size_cap: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    waiting_on_prompt_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    reason_codes_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    forecast: Mapped[ForecastLedger] = relationship(back_populates="decisions")
    reasons: Mapped[list[DecisionReason]] = relationship(
        back_populates="decision", cascade="all, delete-orphan"
    )
    prompt_tasks: Mapped[list[PromptTask]] = relationship(
        back_populates="decision"
    )
    orders: Mapped[list[OrderLedger]] = relationship(
        "OrderLedger", back_populates="decision"
    )


# ---------------------------------------------------------------------------
# 7. DecisionReason
# ---------------------------------------------------------------------------
class DecisionReason(Base):
    __tablename__ = "decision_reason"
    __table_args__ = (
        CheckConstraint(
            "source_of_reason IN ('agent','baseline','manual_bridge','risk','policy')",
            name="ck_decision_reason_source_of_reason",
        ),
        {"schema": "forecasting"},
    )

    decision_reason_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    decision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forecasting.decision_ledger.decision_id"),
        nullable=False,
    )
    source_of_reason: Mapped[str] = mapped_column(Text, nullable=False)
    reason_code: Mapped[str] = mapped_column(Text, nullable=False)
    score_contribution: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 6), nullable=True
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    decision: Mapped[DecisionLedger] = relationship(back_populates="reasons")


# ---------------------------------------------------------------------------
# 8. PromptTask
# ---------------------------------------------------------------------------
class PromptTask(Base):
    __tablename__ = "prompt_task"
    __table_args__ = (
        CheckConstraint(
            "task_type IN ('pretrade_review','novel_event_review',"
            "'source_review','postmortem_review')",
            name="ck_prompt_task_task_type",
        ),
        CheckConstraint(
            "status IN ('created','visible','submitted','parsed',"
            "'needs_reformat','accepted','rejected','expired','canceled')",
            name="ck_prompt_task_status",
        ),
        {"schema": "forecasting"},
    )

    prompt_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    decision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forecasting.decision_ledger.decision_id"),
        nullable=False,
    )
    task_type: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_template_id: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_schema_name: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_bundle_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    deadline_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'created'"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.app_user.user_id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    decision: Mapped[DecisionLedger] = relationship(back_populates="prompt_tasks")
    responses: Mapped[list[PromptResponse]] = relationship(
        back_populates="prompt_task", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# 9. PromptResponse
# ---------------------------------------------------------------------------
class PromptResponse(Base):
    __tablename__ = "prompt_response"
    __table_args__ = (
        UniqueConstraint(
            "prompt_task_id", "submitted_at",
            name="uq_prompt_response_task_submitted",
        ),
        {"schema": "forecasting"},
    )

    prompt_response_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    prompt_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forecasting.prompt_task.prompt_task_id"),
        nullable=False,
    )
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.app_user.user_id"),
        nullable=True,
    )
    model_name_user_entered: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    raw_response: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    schema_valid: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    accepted_for_scoring: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    final_weight: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    parser_version: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    prompt_task: Mapped[PromptTask] = relationship(back_populates="responses")


# ---------------------------------------------------------------------------
# 10. PolicyPackRegistry
# ---------------------------------------------------------------------------
class PolicyPackRegistry(Base):
    __tablename__ = "policy_pack_registry"
    __table_args__ = (
        UniqueConstraint(
            "policy_pack_code", "policy_pack_version",
            name="uq_policy_pack_code_version",
        ),
        CheckConstraint(
            "status IN ('draft','active','deprecated','retired')",
            name="ck_policy_pack_registry_status",
        ),
        {"schema": "forecasting"},
    )

    policy_pack_registry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    policy_pack_code: Mapped[str] = mapped_column(Text, nullable=False)
    policy_pack_version: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'draft'"), nullable=False
    )
    market_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.market_profile.market_profile_id"),
        nullable=True,
    )
    rule_schema_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    rules_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
