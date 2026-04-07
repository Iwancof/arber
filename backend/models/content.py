"""SQLAlchemy ORM models for the `content` schema."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
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


# ---------------------------------------------------------------------------
# 1. DedupCluster
# ---------------------------------------------------------------------------
class DedupCluster(Base):
    __tablename__ = "dedup_cluster"
    __table_args__ = ({"schema": "content"},)

    dedup_cluster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    dedup_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    representative_doc_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.raw_document.raw_document_id", use_alter=True),
        nullable=True,
    )
    cluster_size: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    representative_doc: Mapped[RawDocument | None] = relationship(
        foreign_keys=[representative_doc_id],
        post_update=True,
    )
    documents: Mapped[list[RawDocument]] = relationship(
        back_populates="dedup_cluster",
        foreign_keys="[RawDocument.dedup_cluster_id]",
    )


# ---------------------------------------------------------------------------
# 2. RawDocument
# ---------------------------------------------------------------------------
class RawDocument(Base):
    __tablename__ = "raw_document"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "native_doc_id", name="uq_raw_document_src_native"
        ),
        UniqueConstraint(
            "source_id", "content_hash", name="uq_raw_document_src_hash"
        ),
        CheckConstraint(
            "visibility_scope IN ('internal','restricted','hidden')",
            name="ck_raw_document_visibility_scope",
        ),
        {"schema": "content"},
    )

    raw_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.source_registry.source_id"),
        nullable=False,
    )
    dedup_cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.dedup_cluster.dedup_cluster_id"),
        nullable=True,
    )
    native_doc_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    headline: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    language_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_tier: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    effective_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    correction_of_doc_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.raw_document.raw_document_id"),
        nullable=True,
    )
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    visibility_scope: Mapped[str] = mapped_column(
        Text, server_default=text("'internal'"), nullable=False
    )
    market_profile_hint_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.market_profile.market_profile_id"),
        nullable=True,
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    # relationships
    dedup_cluster: Mapped[DedupCluster | None] = relationship(
        back_populates="documents",
        foreign_keys=[dedup_cluster_id],
    )
    correction_of: Mapped[RawDocument | None] = relationship(
        remote_side="RawDocument.raw_document_id",
        foreign_keys=[correction_of_doc_id],
    )
    asset_links: Mapped[list[DocumentAssetLink]] = relationship(
        back_populates="raw_document", cascade="all, delete-orphan"
    )
    events: Mapped[list[EventLedger]] = relationship(
        back_populates="raw_document"
    )
    evidence_links: Mapped[list[EventEvidenceLink]] = relationship(
        back_populates="raw_document"
    )


# ---------------------------------------------------------------------------
# 3. DocumentAssetLink
# ---------------------------------------------------------------------------
class DocumentAssetLink(Base):
    __tablename__ = "document_asset_link"
    __table_args__ = (
        CheckConstraint(
            "link_type IN ('direct','sector','benchmark','macro','uncertain')",
            name="ck_document_asset_link_type",
        ),
        {"schema": "content"},
    )

    document_asset_link_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    raw_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.raw_document.raw_document_id"),
        nullable=False,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.instrument.instrument_id"),
        nullable=False,
    )
    link_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), server_default=text("0.5"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    raw_document: Mapped[RawDocument] = relationship(back_populates="asset_links")


# ---------------------------------------------------------------------------
# 4. EventLedger
# ---------------------------------------------------------------------------
class EventLedger(Base):
    __tablename__ = "event_ledger"
    __table_args__ = (
        CheckConstraint(
            "direction_hint IN ('positive','negative','neutral','mixed','unknown')",
            name="ck_event_ledger_direction_hint",
        ),
        CheckConstraint(
            "verification_status IN ('extracted','verified','invalid',"
            "'superseded','archived')",
            name="ck_event_ledger_verification_status",
        ),
        {"schema": "content"},
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    raw_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.raw_document.raw_document_id"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    issuer_instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.instrument.instrument_id"),
        nullable=True,
    )
    market_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.market_profile.market_profile_id"),
        nullable=True,
    )
    event_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    direction_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    materiality: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    novelty: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    corroboration_count: Mapped[int] = mapped_column(
        Integer, server_default=text("0"), nullable=False
    )
    extraction_version: Mapped[str] = mapped_column(Text, nullable=False)
    schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    verification_status: Mapped[str] = mapped_column(
        Text, server_default=text("'extracted'"), nullable=False
    )
    supersedes_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.event_ledger.event_id"),
        nullable=True,
    )
    event_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    raw_document: Mapped[RawDocument] = relationship(back_populates="events")
    supersedes: Mapped[EventLedger | None] = relationship(
        remote_side="EventLedger.event_id",
        foreign_keys=[supersedes_event_id],
    )
    asset_impacts: Mapped[list[EventAssetImpact]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    evidence_links: Mapped[list[EventEvidenceLink]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# 5. EventAssetImpact
# ---------------------------------------------------------------------------
class EventAssetImpact(Base):
    __tablename__ = "event_asset_impact"
    __table_args__ = (
        UniqueConstraint(
            "event_id", "instrument_id", "impact_role",
            name="uq_event_asset_impact_evt_inst_role",
        ),
        CheckConstraint(
            "impact_role IN ('issuer','supplier','customer','sector',"
            "'benchmark','macro_proxy','peer')",
            name="ck_event_asset_impact_role",
        ),
        {"schema": "content"},
    )

    event_asset_impact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.event_ledger.event_id"),
        nullable=False,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.instrument.instrument_id"),
        nullable=False,
    )
    impact_role: Mapped[str | None] = mapped_column(Text, nullable=True)
    direction_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), server_default=text("0.5"), nullable=False
    )

    # relationships
    event: Mapped[EventLedger] = relationship(back_populates="asset_impacts")


# ---------------------------------------------------------------------------
# 6. EventEvidenceLink
# ---------------------------------------------------------------------------
class EventEvidenceLink(Base):
    __tablename__ = "event_evidence_link"
    __table_args__ = (
        UniqueConstraint(
            "event_id", "raw_document_id", "evidence_kind", "span_start", "span_end",
            name="uq_event_evidence_link_composite",
        ),
        CheckConstraint(
            "evidence_kind IN ('official','headline','commentary','calendar',"
            "'market_snapshot','manual_note')",
            name="ck_event_evidence_link_kind",
        ),
        {"schema": "content"},
    )

    event_evidence_link_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.event_ledger.event_id"),
        nullable=False,
    )
    raw_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.raw_document.raw_document_id"),
        nullable=False,
    )
    evidence_kind: Mapped[str | None] = mapped_column(Text, nullable=True)
    span_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    span_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), server_default=text("1.0"), nullable=False
    )

    # relationships
    event: Mapped[EventLedger] = relationship(back_populates="evidence_links")
    raw_document: Mapped[RawDocument] = relationship(
        back_populates="evidence_links"
    )
