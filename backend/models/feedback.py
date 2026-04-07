"""SQLAlchemy ORM models for the `feedback` schema."""

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
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


# ---------------------------------------------------------------------------
# 1. OutcomeLedger
# ---------------------------------------------------------------------------
class OutcomeLedger(Base):
    __tablename__ = "outcome_ledger"
    __table_args__ = (
        UniqueConstraint(
            "forecast_id", "horizon_code",
            name="uq_outcome_ledger_forecast_horizon",
        ),
        CheckConstraint(
            "horizon_code IN ('1d','5d','20d','1w','1m')",
            name="ck_outcome_ledger_horizon_code",
        ),
        {"schema": "feedback"},
    )

    outcome_id: Mapped[uuid.UUID] = mapped_column(
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
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    horizon_end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    realized_abs_return: Mapped[Decimal | None] = mapped_column(
        Numeric, nullable=True
    )
    realized_rel_return: Mapped[Decimal | None] = mapped_column(
        Numeric, nullable=True
    )
    benchmark_return: Mapped[Decimal | None] = mapped_column(
        Numeric, nullable=True
    )
    barrier_hit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    mae: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    mfe: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    outcome_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )


# ---------------------------------------------------------------------------
# 2. PostmortemLedger
# ---------------------------------------------------------------------------
class PostmortemLedger(Base):
    __tablename__ = "postmortem_ledger"
    __table_args__ = (
        UniqueConstraint(
            "forecast_id",
            name="uq_postmortem_ledger_forecast",
        ),
        CheckConstraint(
            "verdict IN ('correct','wrong','mixed','insufficient')",
            name="ck_postmortem_ledger_verdict",
        ),
        {"schema": "feedback"},
    )

    postmortem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    forecast_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forecasting.forecast_ledger.forecast_id"),
        nullable=False,
    )
    outcome_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feedback.outcome_ledger.outcome_id"),
        nullable=True,
    )
    verdict: Mapped[str] = mapped_column(Text, nullable=False)
    failure_codes_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    requires_source_review: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    requires_prompt_review: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    judge_version: Mapped[str] = mapped_column(Text, nullable=False)
    postmortem_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ---------------------------------------------------------------------------
# 3. ReliabilityStat
# ---------------------------------------------------------------------------
class ReliabilityStat(Base):
    __tablename__ = "reliability_stat"
    __table_args__ = ({"schema": "feedback"},)

    reliability_stat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    dimension_hash: Mapped[str] = mapped_column(
        Text, unique=True, nullable=False
    )
    market_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.market_profile.market_profile_id"),
        nullable=True,
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.source_registry.source_id"),
        nullable=True,
    )
    event_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    sector: Mapped[str | None] = mapped_column(Text, nullable=True)
    horizon_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_family: Mapped[str | None] = mapped_column(Text, nullable=True)
    manual_model_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_size: Mapped[int] = mapped_column(
        Integer, server_default=text("0"), nullable=False
    )
    hit_rate: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    brier: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    calibration_error: Mapped[Decimal | None] = mapped_column(
        Numeric, nullable=True
    )
    avg_rel_return: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    avg_mae: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    stats_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )


# ---------------------------------------------------------------------------
# 4. ManualModelReliability
# ---------------------------------------------------------------------------
class ManualModelReliability(Base):
    __tablename__ = "manual_model_reliability"
    __table_args__ = (
        UniqueConstraint(
            "model_name", "market_profile_id", "event_type", "horizon_code",
            name="uq_manual_model_reliability_dims",
        ),
        {"schema": "feedback"},
    )

    manual_model_reliability_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    market_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.market_profile.market_profile_id"),
        nullable=True,
    )
    event_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    horizon_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_size: Mapped[int] = mapped_column(
        Integer, server_default=text("0"), nullable=False
    )
    schema_valid_rate: Mapped[Decimal | None] = mapped_column(
        Numeric, nullable=True
    )
    accepted_rate: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    hit_rate: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    brier: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    calibration_error: Mapped[Decimal | None] = mapped_column(
        Numeric, nullable=True
    )
    avg_rel_return: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
