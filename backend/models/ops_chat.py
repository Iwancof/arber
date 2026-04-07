"""SQLAlchemy ORM models for the ops_chat schema.

Tables: chat_session, chat_message, context_capsule,
context_capsule_source_ref, chat_intent,
chat_action_proposal, chat_action_execution,
chat_memory_note, chat_mode_transition.
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
    Numeric,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


# -------------------------------------------------------
# 1. ChatSession
# -------------------------------------------------------
class ChatSession(Base):
    __tablename__ = "chat_session"
    __table_args__ = (
        CheckConstraint(
            "session_mode IN ("
            "'observe','advise','operate','implement'"
            ")",
            name="ck_chat_session_mode",
        ),
        CheckConstraint(
            "status IN ('open','paused','closed')",
            name="ck_chat_session_status",
        ),
        {"schema": "ops_chat"},
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    channel: Mapped[str] = mapped_column(
        Text,
        server_default=text("'claude_code'"),
        nullable=False,
    )
    actor_user_id: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    actor_display_name: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    session_mode: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    title: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    active_scope_type: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    active_scope_key: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    trace_id: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    correlation_id: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_activity_at: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )
    )
    closed_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(timezone=True), nullable=True,
        )
    )
    status: Mapped[str] = mapped_column(
        Text,
        server_default=text("'open'"),
        nullable=False,
    )

    # relationships
    messages: Mapped[list[ChatMessage]] = (
        relationship(
            back_populates="session",
            cascade="all, delete-orphan",
        )
    )
    intents: Mapped[list[ChatIntent]] = (
        relationship(
            back_populates="session",
            cascade="all, delete-orphan",
        )
    )
    mode_transitions: Mapped[
        list[ChatModeTransition]
    ] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    memory_notes: Mapped[
        list[ChatMemoryNote]
    ] = relationship(
        back_populates="source_session",
        foreign_keys=(
            "ChatMemoryNote.source_session_id"
        ),
    )


# -------------------------------------------------------
# 2. ChatMessage
# -------------------------------------------------------
class ChatMessage(Base):
    __tablename__ = "chat_message"
    __table_args__ = (
        CheckConstraint(
            "role IN ("
            "'system','user','assistant','tool'"
            ")",
            name="ck_chat_message_role",
        ),
        {"schema": "ops_chat"},
    )

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "ops_chat.chat_session.session_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    content_md: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    content_json: Mapped[dict | None] = (
        mapped_column(JSONB, nullable=True)
    )
    provenance_json: Mapped[dict | None] = (
        mapped_column(JSONB, nullable=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # relationships
    session: Mapped[ChatSession] = relationship(
        back_populates="messages",
    )
    intents: Mapped[list[ChatIntent]] = (
        relationship(
            back_populates="source_message",
            cascade="all, delete-orphan",
        )
    )


# -------------------------------------------------------
# 3. ContextCapsule
# -------------------------------------------------------
class ContextCapsule(Base):
    __tablename__ = "context_capsule"
    __table_args__ = (
        CheckConstraint(
            "status IN ("
            "'fresh','stale','degraded','failed'"
            ")",
            name="ck_context_capsule_status",
        ),
        {"schema": "ops_chat"},
    )

    capsule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    capsule_type: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    scope_key: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    fresh_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Text,
        server_default=text("'fresh'"),
        nullable=False,
    )
    summary_md: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    summary_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
    )
    evidence_refs: Mapped[dict] = mapped_column(
        JSONB,
        server_default=text("'[]'::jsonb"),
        nullable=False,
    )
    trace_id: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    created_by: Mapped[str] = mapped_column(
        Text,
        server_default=text("'capsule_assembler'"),
        nullable=False,
    )

    # relationships
    source_refs: Mapped[
        list[ContextCapsuleSourceRef]
    ] = relationship(
        back_populates="capsule",
        cascade="all, delete-orphan",
    )


# -------------------------------------------------------
# 4. ContextCapsuleSourceRef
# -------------------------------------------------------
class ContextCapsuleSourceRef(Base):
    __tablename__ = "context_capsule_source_ref"
    __table_args__ = (
        {"schema": "ops_chat"},
    )

    capsule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "ops_chat.context_capsule.capsule_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    ref_kind: Mapped[str] = mapped_column(
        Text, primary_key=True,
    )
    ref_id: Mapped[str] = mapped_column(
        Text, primary_key=True,
    )

    # relationships
    capsule: Mapped[ContextCapsule] = relationship(
        back_populates="source_refs",
    )


# -------------------------------------------------------
# 5. ChatIntent
# -------------------------------------------------------
class ChatIntent(Base):
    __tablename__ = "chat_intent"
    __table_args__ = (
        CheckConstraint(
            "status IN ("
            "'parsed','draft','proposed',"
            "'executed','rejected','failed'"
            ")",
            name="ck_chat_intent_status",
        ),
        {"schema": "ops_chat"},
    )

    intent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "ops_chat.chat_session.session_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    source_message_id: Mapped[uuid.UUID] = (
        mapped_column(
            UUID(as_uuid=True),
            ForeignKey(
                "ops_chat.chat_message.message_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        )
    )
    intent_type: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False,
    )
    intent_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Text,
        server_default=text("'parsed'"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # relationships
    session: Mapped[ChatSession] = relationship(
        back_populates="intents",
    )
    source_message: Mapped[ChatMessage] = (
        relationship(back_populates="intents")
    )
    proposals: Mapped[
        list[ChatActionProposal]
    ] = relationship(
        back_populates="intent",
        cascade="all, delete-orphan",
    )


# -------------------------------------------------------
# 6. ChatActionProposal
# -------------------------------------------------------
class ChatActionProposal(Base):
    __tablename__ = "chat_action_proposal"
    __table_args__ = (
        CheckConstraint(
            "risk_tier IN ("
            "'low','medium','high','critical'"
            ")",
            name="ck_chat_proposal_risk_tier",
        ),
        CheckConstraint(
            "status IN ("
            "'pending','confirmed','rejected',"
            "'executed','expired','failed'"
            ")",
            name="ck_chat_proposal_status",
        ),
        {"schema": "ops_chat"},
    )

    proposal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    intent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "ops_chat.chat_intent.intent_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    proposal_type: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    risk_tier: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    requires_confirmation: Mapped[bool] = (
        mapped_column(
            Boolean,
            server_default=text("true"),
            nullable=False,
        )
    )
    expires_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(timezone=True), nullable=True,
        )
    )
    summary_md: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    diff_json: Mapped[dict | None] = (
        mapped_column(JSONB, nullable=True)
    )
    command_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
    )
    blocked_by: Mapped[dict] = mapped_column(
        JSONB,
        server_default=text("'[]'::jsonb"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Text,
        server_default=text("'pending'"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    confirmed_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(timezone=True), nullable=True,
        )
    )
    confirmed_by: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )

    # relationships
    intent: Mapped[ChatIntent] = relationship(
        back_populates="proposals",
    )
    executions: Mapped[
        list[ChatActionExecution]
    ] = relationship(
        back_populates="proposal",
        cascade="all, delete-orphan",
    )


# -------------------------------------------------------
# 7. ChatActionExecution
# -------------------------------------------------------
class ChatActionExecution(Base):
    __tablename__ = "chat_action_execution"
    __table_args__ = (
        CheckConstraint(
            "result_status IN ("
            "'success','partial','failed','rejected'"
            ")",
            name="ck_chat_execution_result_status",
        ),
        {"schema": "ops_chat"},
    )

    execution_id: Mapped[uuid.UUID] = (
        mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
        )
    )
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "ops_chat.chat_action_proposal"
            ".proposal_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    executed_by: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    execution_mode: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    result_status: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    result_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
    )
    linked_event_refs: Mapped[dict] = (
        mapped_column(
            JSONB,
            server_default=text("'[]'::jsonb"),
            nullable=False,
        )
    )
    trace_id: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # relationships
    proposal: Mapped[ChatActionProposal] = (
        relationship(back_populates="executions")
    )


# -------------------------------------------------------
# 8. ChatMemoryNote
# -------------------------------------------------------
class ChatMemoryNote(Base):
    __tablename__ = "chat_memory_note"
    __table_args__ = (
        CheckConstraint(
            "status IN ("
            "'active','superseded','archived'"
            ")",
            name="ck_chat_memory_note_status",
        ),
        {"schema": "ops_chat"},
    )

    note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    scope_type: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    scope_key: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    note_type: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    source_session_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "ops_chat.chat_session.session_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    source_message_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "ops_chat.chat_message.message_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    body_md: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    body_json: Mapped[dict | None] = (
        mapped_column(JSONB, nullable=True)
    )
    status: Mapped[str] = mapped_column(
        Text,
        server_default=text("'active'"),
        nullable=False,
    )
    created_by: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # relationships
    source_session: Mapped[
        ChatSession | None
    ] = relationship(
        back_populates="memory_notes",
        foreign_keys=[source_session_id],
    )


# -------------------------------------------------------
# 9. ChatModeTransition
# -------------------------------------------------------
class ChatModeTransition(Base):
    __tablename__ = "chat_mode_transition"
    __table_args__ = (
        {"schema": "ops_chat"},
    )

    transition_id: Mapped[uuid.UUID] = (
        mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
        )
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "ops_chat.chat_session.session_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    from_mode: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    to_mode: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    approved_by: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    reason_md: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )
    approved_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(timezone=True), nullable=True,
        )
    )
    expires_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(timezone=True), nullable=True,
        )
    )
    trace_id: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # relationships
    session: Mapped[ChatSession] = relationship(
        back_populates="mode_transitions",
    )
