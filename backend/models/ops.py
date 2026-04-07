"""SQLAlchemy ORM models for the `ops` schema."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


# ---------------------------------------------------------------------------
# 1. WatcherInstance
# ---------------------------------------------------------------------------
class WatcherInstance(Base):
    __tablename__ = "watcher_instance"
    __table_args__ = (
        CheckConstraint(
            "execution_mode IN ('replay','shadow','paper','micro_live','live')",
            name="ck_watcher_instance_execution_mode",
        ),
        CheckConstraint(
            "status IN ('running','stopped','degraded','failed')",
            name="ck_watcher_instance_status",
        ),
        {"schema": "ops"},
    )

    watcher_instance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.source_registry.source_id"),
        nullable=False,
    )
    watch_plan_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.watch_plan_item.watch_plan_item_id"),
        nullable=True,
    )
    execution_mode: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'running'"), nullable=False
    )
    error_count: Mapped[int] = mapped_column(
        Integer, server_default=text("0"), nullable=False
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )


# ---------------------------------------------------------------------------
# 2. AuditLog
# ---------------------------------------------------------------------------
class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        CheckConstraint(
            "actor_type IN ('user','system')",
            name="ck_audit_log_actor_type",
        ),
        {"schema": "ops"},
    )

    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    actor_type: Mapped[str] = mapped_column(Text, nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.app_user.user_id"),
        nullable=True,
    )
    actor_label: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[str] = mapped_column(Text, nullable=False)
    before_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ---------------------------------------------------------------------------
# 3. KillSwitch
# ---------------------------------------------------------------------------
class KillSwitch(Base):
    __tablename__ = "kill_switch"
    __table_args__ = (
        UniqueConstraint(
            "scope_type", "scope_key",
            name="uq_kill_switch_scope",
        ),
        CheckConstraint(
            "scope_type IN ("
            "'global','market','strategy','source','broker',"
            "'trade_halt_global','reduce_only_global',"
            "'decision_halt','source_ingest_pause','full_freeze'"
            ")",
            name="ck_kill_switch_scope_type",
        ),
        {"schema": "ops"},
    )

    kill_switch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    scope_type: Mapped[str] = mapped_column(Text, nullable=False)
    scope_key: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    activated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.app_user.user_id"),
        nullable=True,
    )
    activated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    cleared_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ---------------------------------------------------------------------------
# 4. SystemConfig
# ---------------------------------------------------------------------------
class SystemConfig(Base):
    __tablename__ = "system_config"
    __table_args__ = ({"schema": "ops"},)

    config_key: Mapped[str] = mapped_column(Text, primary_key=True)
    config_value_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.app_user.user_id"),
        nullable=True,
    )


# ---------------------------------------------------------------------------
# 5. JobRun
# ---------------------------------------------------------------------------
class JobRun(Base):
    __tablename__ = "job_run"
    __table_args__ = (
        CheckConstraint(
            "execution_mode IN ('replay','shadow','paper','micro_live','live')",
            name="ck_job_run_execution_mode",
        ),
        CheckConstraint(
            "status IN ('queued','running','succeeded','failed','canceled')",
            name="ck_job_run_status",
        ),
        {"schema": "ops"},
    )

    job_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    job_type: Mapped[str] = mapped_column(Text, nullable=False)
    execution_mode: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'queued'"), nullable=False
    )
    requested_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.app_user.user_id"),
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    job_args_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    result_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )


# ---------------------------------------------------------------------------
# 6. OutboxEvent
# ---------------------------------------------------------------------------
class OutboxEvent(Base):
    __tablename__ = "outbox_event"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','published','failed','dead_letter')",
            name="ck_outbox_event_status",
        ),
        {"schema": "ops"},
    )

    outbox_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    partition_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_name: Mapped[str] = mapped_column(Text, nullable=False)
    event_version: Mapped[str] = mapped_column(Text, nullable=False)
    schema_name: Mapped[str] = mapped_column(Text, nullable=False)
    schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    trace_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'pending'"), nullable=False
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer, server_default=text("0"), nullable=False
    )
    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
