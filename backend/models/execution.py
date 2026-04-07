"""SQLAlchemy ORM models for the `execution` schema."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.forecasting import DecisionLedger

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


# ---------------------------------------------------------------------------
# 1. OrderLedger
# ---------------------------------------------------------------------------
class OrderLedger(Base):
    __tablename__ = "order_ledger"
    __table_args__ = (
        UniqueConstraint("client_order_id", name="uq_order_ledger_client_order_id"),
        CheckConstraint(
            "execution_mode IN ('replay','shadow','paper','micro_live','live')",
            name="ck_order_ledger_execution_mode",
        ),
        CheckConstraint(
            "side IN ('buy','sell')",
            name="ck_order_ledger_side",
        ),
        CheckConstraint(
            "order_type IN ('market','limit','stop','stop_limit')",
            name="ck_order_ledger_order_type",
        ),
        CheckConstraint(
            "session_type IN ('premarket','regular','postmarket','overnight')",
            name="ck_order_ledger_session_type",
        ),
        CheckConstraint(
            "status IN ('new','accepted','partially_filled','filled',"
            "'canceled','rejected','expired')",
            name="ck_order_ledger_status",
        ),
        {"schema": "execution"},
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    decision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forecasting.decision_ledger.decision_id"),
        nullable=False,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.instrument.instrument_id"),
        nullable=False,
    )
    execution_mode: Mapped[str] = mapped_column(Text, nullable=False)
    broker_name: Mapped[str] = mapped_column(Text, nullable=False)
    client_order_id: Mapped[str] = mapped_column(Text, nullable=False)
    broker_order_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    side: Mapped[str] = mapped_column(Text, nullable=False)
    order_type: Mapped[str] = mapped_column(Text, nullable=False)
    time_in_force: Mapped[str] = mapped_column(Text, nullable=False)
    session_type: Mapped[str] = mapped_column(Text, nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    limit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    stop_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'new'"), nullable=False
    )
    status_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    # relationships
    decision: Mapped[DecisionLedger] = relationship(
        "DecisionLedger", back_populates="orders"
    )
    fills: Mapped[list[ExecutionFill]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# 2. ExecutionFill
# ---------------------------------------------------------------------------
class ExecutionFill(Base):
    __tablename__ = "execution_fill"
    __table_args__ = (
        CheckConstraint(
            "fill_source IN ('replay','paper','live','adjusted_overlay')",
            name="ck_execution_fill_fill_source",
        ),
        {"schema": "execution"},
    )

    fill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("execution.order_ledger.order_id"),
        nullable=False,
    )
    fill_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    fill_price: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    fill_qty: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    fee_estimate: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    liquidity_flag: Mapped[str | None] = mapped_column(Text, nullable=True)
    fill_source: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    # relationships
    order: Mapped[OrderLedger] = relationship(back_populates="fills")


# ---------------------------------------------------------------------------
# 3. PositionSnapshot
# ---------------------------------------------------------------------------
class PositionSnapshot(Base):
    __tablename__ = "position_snapshot"
    __table_args__ = (
        CheckConstraint(
            "execution_mode IN ('replay','shadow','paper','micro_live','live')",
            name="ck_position_snapshot_execution_mode",
        ),
        {"schema": "execution"},
    )

    position_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    as_of: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    execution_mode: Mapped[str] = mapped_column(Text, nullable=False)
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.instrument.instrument_id"),
        nullable=False,
    )
    position_qty: Mapped[Decimal] = mapped_column(
        Numeric(18, 8), server_default=text("0"), nullable=False
    )
    average_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    mark_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    unrealized_pnl: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    realized_pnl: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    snapshot_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
