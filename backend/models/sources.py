"""SQLAlchemy ORM models for the `sources` schema."""

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
# 1. SourceRegistry
# ---------------------------------------------------------------------------
class SourceRegistry(Base):
    __tablename__ = "source_registry"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('official','vendor','exchange','regulator',"
            "'macro_calendar','community','internal')",
            name="ck_source_registry_source_type",
        ),
        CheckConstraint(
            "adapter_type IN ('rss','json_api','html_scrape','websocket',"
            "'calendar','file_drop','manual_entry')",
            name="ck_source_registry_adapter_type",
        ),
        CheckConstraint(
            "trust_tier IN ('official','high_vendor','medium_vendor',"
            "'low_vendor','experimental')",
            name="ck_source_registry_trust_tier",
        ),
        CheckConstraint(
            "latency_class IN ('realtime','scheduled','delayed','batch')",
            name="ck_source_registry_latency_class",
        ),
        CheckConstraint(
            "status IN ('active','disabled','retired')",
            name="ck_source_registry_status",
        ),
        {"schema": "sources"},
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    source_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    adapter_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    trust_tier: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_class: Mapped[str | None] = mapped_column(Text, nullable=True)
    auth_requirements_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    coverage_tags_json: Mapped[list] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    markets_json: Mapped[list] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    languages_json: Mapped[list] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    retention_days: Mapped[int] = mapped_column(Integer, server_default=text("365"))
    legal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_team: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'active'"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    endpoints: Mapped[list[SourceEndpoint]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )
    bundle_items: Mapped[list[SourceBundleItem]] = relationship(
        back_populates="source"
    )
    watch_plan_items: Mapped[list[WatchPlanItem]] = relationship(
        back_populates="source"
    )


# ---------------------------------------------------------------------------
# 2. SourceEndpoint
# ---------------------------------------------------------------------------
class SourceEndpoint(Base):
    __tablename__ = "source_endpoint"
    __table_args__ = (
        UniqueConstraint("source_id", "endpoint_name", name="uq_source_endpoint_src_name"),
        CheckConstraint(
            "endpoint_type IN ('rss','json_api','html','websocket','calendar','file')",
            name="ck_source_endpoint_type",
        ),
        {"schema": "sources"},
    )

    source_endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.source_registry.source_id"),
        nullable=False,
    )
    endpoint_name: Mapped[str] = mapped_column(Text, nullable=False)
    endpoint_url: Mapped[str] = mapped_column(Text, nullable=False)
    endpoint_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    auth_profile: Mapped[str | None] = mapped_column(Text, nullable=True)
    polling_interval_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rate_limit_per_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    # relationships
    source: Mapped[SourceRegistry] = relationship(back_populates="endpoints")


# ---------------------------------------------------------------------------
# 3. SourceBundle
# ---------------------------------------------------------------------------
class SourceBundle(Base):
    __tablename__ = "source_bundle"
    __table_args__ = (
        CheckConstraint(
            "bundle_scope IN ('market_core','sector_overlay','event_overlay','temporary')",
            name="ck_source_bundle_scope",
        ),
        {"schema": "sources"},
    )

    source_bundle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    bundle_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    market_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.market_profile.market_profile_id"),
        nullable=True,
    )
    bundle_scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    applies_to_asset_class: Mapped[str | None] = mapped_column(Text, nullable=True)
    applies_to_sector: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    # relationships
    items: Mapped[list[SourceBundleItem]] = relationship(
        back_populates="bundle", cascade="all, delete-orphan"
    )
    watch_plan_items: Mapped[list[WatchPlanItem]] = relationship(
        back_populates="source_bundle"
    )


# ---------------------------------------------------------------------------
# 4. SourceBundleItem
# ---------------------------------------------------------------------------
class SourceBundleItem(Base):
    __tablename__ = "source_bundle_item"
    __table_args__ = (
        UniqueConstraint(
            "source_bundle_id", "source_id", name="uq_source_bundle_item_bundle_src"
        ),
        {"schema": "sources"},
    )

    source_bundle_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    source_bundle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.source_bundle.source_bundle_id"),
        nullable=False,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.source_registry.source_id"),
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(SmallInteger, server_default=text("100"))
    activation_rule_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    ttl_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))

    # relationships
    bundle: Mapped[SourceBundle] = relationship(back_populates="items")
    source: Mapped[SourceRegistry] = relationship(back_populates="bundle_items")


# ---------------------------------------------------------------------------
# 5. SourceCandidate
# ---------------------------------------------------------------------------
class SourceCandidate(Base):
    __tablename__ = "source_candidate"
    __table_args__ = (
        CheckConstraint(
            "proposal_type IN ('new_source_candidate','bundle_change','endpoint_change')",
            name="ck_source_candidate_proposal_type",
        ),
        CheckConstraint(
            "proposed_by_type IN ('llm','user','system')",
            name="ck_source_candidate_proposed_by_type",
        ),
        CheckConstraint(
            "status IN ('candidate','provisional','validated','production',"
            "'retired','rejected')",
            name="ck_source_candidate_status",
        ),
        {"schema": "sources"},
    )

    source_candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    proposed_source_code: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_adapter_type: Mapped[str] = mapped_column(Text, nullable=False)
    proposal_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_now: Mapped[str] = mapped_column(Text, nullable=False)
    expected_coverage_json: Mapped[list] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    linked_market_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.market_profile.market_profile_id"),
        nullable=True,
    )
    linked_bundle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.source_bundle.source_bundle_id"),
        nullable=True,
    )
    proposed_by_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_by: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'candidate'"), nullable=False
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ---------------------------------------------------------------------------
# 6. UniverseSet
# ---------------------------------------------------------------------------
class UniverseSet(Base):
    __tablename__ = "universe_set"
    __table_args__ = ({"schema": "sources"},)

    universe_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    universe_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    market_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.market_profile.market_profile_id"),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    selection_rule_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    members: Mapped[list[UniverseMember]] = relationship(
        back_populates="universe_set", cascade="all, delete-orphan"
    )
    watch_plans: Mapped[list[WatchPlan]] = relationship(
        back_populates="universe_set"
    )


# ---------------------------------------------------------------------------
# 7. UniverseMember
# ---------------------------------------------------------------------------
class UniverseMember(Base):
    __tablename__ = "universe_member"
    __table_args__ = ({"schema": "sources"},)

    universe_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.universe_set.universe_set_id"),
        primary_key=True,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.instrument.instrument_id"),
        primary_key=True,
    )
    weight_hint: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 8), nullable=True
    )
    tags_json: Mapped[list] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    removed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # relationships
    universe_set: Mapped[UniverseSet] = relationship(back_populates="members")


# ---------------------------------------------------------------------------
# 8. WatchPlan
# ---------------------------------------------------------------------------
class WatchPlan(Base):
    __tablename__ = "watch_plan"
    __table_args__ = (
        CheckConstraint(
            "execution_mode IN ('replay','shadow','paper','micro_live','live')",
            name="ck_watch_plan_execution_mode",
        ),
        {"schema": "sources"},
    )

    watch_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    market_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.market_profile.market_profile_id"),
        nullable=False,
    )
    universe_set_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.universe_set.universe_set_id"),
        nullable=True,
    )
    execution_mode: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_reason_codes_json: Mapped[list] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    portfolio_tags_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    generated_by: Mapped[str] = mapped_column(
        Text, server_default=text("'system'"), nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))

    # relationships
    universe_set: Mapped[UniverseSet | None] = relationship(
        back_populates="watch_plans"
    )
    items: Mapped[list[WatchPlanItem]] = relationship(
        back_populates="watch_plan", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# 9. WatchPlanItem
# ---------------------------------------------------------------------------
class WatchPlanItem(Base):
    __tablename__ = "watch_plan_item"
    __table_args__ = (
        UniqueConstraint(
            "watch_plan_id", "source_id", name="uq_watch_plan_item_plan_src"
        ),
        CheckConstraint(
            "state IN ('planned','running','paused','failed','completed')",
            name="ck_watch_plan_item_state",
        ),
        {"schema": "sources"},
    )

    watch_plan_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    watch_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.watch_plan.watch_plan_id"),
        nullable=False,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.source_registry.source_id"),
        nullable=False,
    )
    source_bundle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.source_bundle.source_bundle_id"),
        nullable=True,
    )
    priority: Mapped[int] = mapped_column(SmallInteger, server_default=text("100"))
    is_temporary: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    ttl_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    state: Mapped[str] = mapped_column(
        Text, server_default=text("'planned'"), nullable=False
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    # relationships
    watch_plan: Mapped[WatchPlan] = relationship(back_populates="items")
    source: Mapped[SourceRegistry] = relationship(back_populates="watch_plan_items")
    source_bundle: Mapped[SourceBundle | None] = relationship(
        back_populates="watch_plan_items"
    )
