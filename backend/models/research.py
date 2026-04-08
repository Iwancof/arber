"""SQLAlchemy ORM models for the research_ops schema.

Research Scout / Autonomous News Exploration:
  - ResearchCase, ResearchScope, ResearchJob
  - ResearchQueryPlan, ResearchEvidence
  - ResearchBrief, SymbolDossierSnapshot
  - CandidateSymbol, RelatedSymbolEdge
  - ResearchFeedback
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
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
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from backend.models.base import Base


# -----------------------------------------------------------
# 1. ResearchCase
# -----------------------------------------------------------
class ResearchCase(Base):
    __tablename__ = "research_case"
    __table_args__ = {"schema": "research_ops"}

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    case_type: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    market_code: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    primary_symbol: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    benchmark_symbol: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    title: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    priority: Mapped[int] = mapped_column(
        SmallInteger,
        server_default=text("50"),
        nullable=False,
    )
    trigger_reason: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    current_hypothesis_summary: Mapped[
        str | None
    ] = mapped_column(Text, nullable=True)
    current_question_summary: Mapped[
        str | None
    ] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    correlation_id: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
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
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_updated_at: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )
    )

    # relationships
    scopes: Mapped[list[ResearchScope]] = (
        relationship(back_populates="research_case")
    )
    jobs: Mapped[list[ResearchJob]] = (
        relationship(back_populates="research_case")
    )
    evidence: Mapped[list[ResearchEvidence]] = (
        relationship(back_populates="research_case")
    )
    briefs: Mapped[list[ResearchBrief]] = (
        relationship(back_populates="research_case")
    )


# -----------------------------------------------------------
# 2. ResearchScope
# -----------------------------------------------------------
class ResearchScope(Base):
    __tablename__ = "research_scope"
    __table_args__ = {"schema": "research_ops"}

    scope_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "research_ops.research_case.case_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    scope_type: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    scope_key: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    scope_role: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # relationships
    research_case: Mapped[ResearchCase] = (
        relationship(back_populates="scopes")
    )


# -----------------------------------------------------------
# 3. ResearchJob
# -----------------------------------------------------------
class ResearchJob(Base):
    __tablename__ = "research_job"
    __table_args__ = {"schema": "research_ops"}

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    case_id: Mapped[uuid.UUID | None] = (
        mapped_column(
            UUID(as_uuid=True),
            ForeignKey(
                "research_ops.research_case.case_id",
                ondelete="SET NULL",
            ),
            nullable=True,
        )
    )
    job_type: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    trigger_type: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    budget_class: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    worker_adapter: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    prompt_version: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    input_hash: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    result_summary: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    trace_id: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    correlation_id: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    scheduled_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(timezone=True), nullable=True,
        )
    )
    started_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(timezone=True), nullable=True,
        )
    )
    finished_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(timezone=True), nullable=True,
        )
    )
    next_run_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(timezone=True), nullable=True,
        )
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # relationships
    research_case: Mapped[
        ResearchCase | None
    ] = relationship(back_populates="jobs")
    query_plans: Mapped[
        list[ResearchQueryPlan]
    ] = relationship(back_populates="research_job")


# -----------------------------------------------------------
# 4. ResearchQueryPlan
# -----------------------------------------------------------
class ResearchQueryPlan(Base):
    __tablename__ = "research_query_plan"
    __table_args__ = {"schema": "research_ops"}

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "research_ops.research_job.job_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    query_kind: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    source_filter_json: Mapped[dict] = (
        mapped_column(
            JSONB,
            server_default=text("'{}'::jsonb"),
            nullable=False,
        )
    )
    query_text: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    time_window_start: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    time_window_end: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    max_docs: Mapped[int] = mapped_column(
        Integer,
        server_default=text("20"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # relationships
    research_job: Mapped[ResearchJob] = (
        relationship(back_populates="query_plans")
    )


# -----------------------------------------------------------
# 5. ResearchEvidence
# -----------------------------------------------------------
class ResearchEvidence(Base):
    __tablename__ = "research_evidence"
    __table_args__ = {"schema": "research_ops"}

    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "research_ops.research_case.case_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    source_doc_id: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    source_type: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    evidence_role: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    symbol: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    event_type: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    published_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(timezone=True), nullable=True,
        )
    )
    relevance_score: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(5, 4), nullable=True,
    )
    novelty_score: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(5, 4), nullable=True,
    )
    reliability_score: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(5, 4), nullable=True,
    )
    summary: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    quote_spans_json: Mapped[dict] = (
        mapped_column(
            JSONB,
            server_default=text("'[]'::jsonb"),
            nullable=False,
        )
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # relationships
    research_case: Mapped[ResearchCase] = (
        relationship(back_populates="evidence")
    )


# -----------------------------------------------------------
# 6. ResearchBrief
# -----------------------------------------------------------
class ResearchBrief(Base):
    __tablename__ = "research_brief"
    __table_args__ = {"schema": "research_ops"}

    brief_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "research_ops.research_case.case_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    brief_kind: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        server_default=text("1"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    brief_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
    )
    expires_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(timezone=True), nullable=True,
        )
    )
    trace_id: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # relationships
    research_case: Mapped[ResearchCase] = (
        relationship(back_populates="briefs")
    )


# -----------------------------------------------------------
# 7. SymbolDossierSnapshot
# -----------------------------------------------------------
class SymbolDossierSnapshot(Base):
    __tablename__ = "symbol_dossier_snapshot"
    __table_args__ = {"schema": "research_ops"}

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    market_code: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    symbol: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    asof: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    watch_status: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    benchmark_symbol: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    current_thesis: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    payload_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
    )
    quality_score: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(5, 4), nullable=True,
    )
    coverage_score: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(5, 4), nullable=True,
    )
    research_depth_score: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(5, 4), nullable=True,
    )
    freshness_class: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    source_case_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "research_ops.research_case.case_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


# -----------------------------------------------------------
# 8. CandidateSymbol
# -----------------------------------------------------------
class CandidateSymbol(Base):
    __tablename__ = "candidate_symbol"
    __table_args__ = {"schema": "research_ops"}

    candidate_id: Mapped[uuid.UUID] = (
        mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=text(
                "gen_random_uuid()"
            ),
        )
    )
    market_code: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    symbol: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    discovered_from_case_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "research_ops.research_case.case_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    discovered_from_event_ref: Mapped[
        str | None
    ] = mapped_column(Text, nullable=True)
    relation_to_watchlist: Mapped[str] = (
        mapped_column(Text, nullable=False)
    )
    candidate_reason_codes: Mapped[dict] = (
        mapped_column(
            JSONB,
            server_default=text("'[]'::jsonb"),
            nullable=False,
        )
    )
    discovery_score: Mapped[Decimal] = (
        mapped_column(
            Numeric(5, 4),
            server_default=text("0.0000"),
            nullable=False,
        )
    )
    promotion_score: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(5, 4), nullable=True,
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    first_seen_at: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )
    )
    last_seen_at: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )
    )
    promoted_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(timezone=True), nullable=True,
        )
    )
    rejected_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(timezone=True), nullable=True,
        )
    )
    decision_note: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    trace_id: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    correlation_id: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


# -----------------------------------------------------------
# 9. RelatedSymbolEdge
# -----------------------------------------------------------
class RelatedSymbolEdge(Base):
    __tablename__ = "related_symbol_edge"
    __table_args__ = (
        UniqueConstraint(
            "market_code",
            "source_symbol",
            "target_symbol",
            "relation_type",
            name=(
                "uq_related_symbol_edge_"
                "market_src_tgt_rel"
            ),
        ),
        {"schema": "research_ops"},
    )

    edge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    market_code: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    source_symbol: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    target_symbol: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    relation_type: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        server_default=text("0.5000"),
        nullable=False,
    )
    provenance_json: Mapped[dict] = (
        mapped_column(
            JSONB,
            server_default=text("'{}'::jsonb"),
            nullable=False,
        )
    )
    first_seen_at: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )
    )
    last_validated_at: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )
    )


# -----------------------------------------------------------
# 10. ResearchFeedback
# -----------------------------------------------------------
class ResearchFeedback(Base):
    __tablename__ = "research_feedback"
    __table_args__ = {"schema": "research_ops"}

    feedback_id: Mapped[uuid.UUID] = (
        mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=text(
                "gen_random_uuid()"
            ),
        )
    )
    target_type: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False,
    )
    feedback_kind: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    feedback_json: Mapped[dict] = mapped_column(
        JSONB,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
    created_by: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
