"""Pydantic schemas for Ops Chat Copilot API.

Covers: sessions, messages, context capsules,
intents, action proposals, executions,
memory notes, mode transitions, and timeline.
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


# -------------------------------------------------------
# ChatSession
# -------------------------------------------------------
class ChatSessionCreate(OrmBase):
    """Body for creating a chat session."""

    session_mode: str
    scope_entity_type: str | None = None
    scope_entity_id: str | None = None


class ChatSessionRead(OrmBase):
    """Read schema for a chat session."""

    session_id: UUID
    channel: str
    actor_user_id: str
    actor_display_name: str | None = None
    session_mode: str
    title: str | None = None
    active_scope_type: str | None = None
    active_scope_key: str | None = None
    trace_id: str
    correlation_id: str | None = None
    started_at: datetime
    last_activity_at: datetime
    closed_at: datetime | None = None
    status: str


class ChatSessionList(PaginatedResponse):
    """Paginated list of chat sessions."""

    items: list[ChatSessionRead]


# -------------------------------------------------------
# ChatMessage
# -------------------------------------------------------
class ChatMessageCreate(OrmBase):
    """Body for appending a user message."""

    content_md: str


class ChatMessageRead(OrmBase):
    """Read schema for a chat message."""

    message_id: UUID
    session_id: UUID
    role: str
    content_md: str
    content_json: dict[str, Any] | None = None
    provenance_json: (
        dict[str, Any] | None
    ) = None
    created_at: datetime


# -------------------------------------------------------
# ContextCapsule
# -------------------------------------------------------
class ContextCapsuleRead(OrmBase):
    """Read schema for a context capsule."""

    capsule_id: UUID
    capsule_type: str
    scope_key: str
    generated_at: datetime
    fresh_until: datetime
    status: str
    summary_md: str
    summary_json: dict[str, Any]
    evidence_refs: list[Any] = Field(
        default_factory=list,
    )
    trace_id: str
    created_by: str


# -------------------------------------------------------
# ChatIntent
# -------------------------------------------------------
class ChatIntentRead(OrmBase):
    """Read schema for a parsed chat intent."""

    intent_id: UUID
    session_id: UUID
    source_message_id: UUID
    intent_type: str
    confidence: Decimal
    intent_json: dict[str, Any]
    status: str
    created_at: datetime


# -------------------------------------------------------
# ActionProposal
# -------------------------------------------------------
class ActionProposalRead(OrmBase):
    """Read schema for an action proposal."""

    proposal_id: UUID
    intent_id: UUID
    proposal_type: str
    risk_tier: str
    requires_confirmation: bool
    expires_at: datetime | None = None
    summary_md: str
    diff_json: dict[str, Any] | None = None
    command_json: dict[str, Any]
    blocked_by: list[Any] = Field(
        default_factory=list,
    )
    status: str
    created_at: datetime
    confirmed_at: datetime | None = None
    confirmed_by: str | None = None


class ActionProposalConfirm(OrmBase):
    """Body for confirming a proposal."""

    typed_confirmation: str | None = None


class ActionProposalReject(OrmBase):
    """Body for rejecting a proposal."""

    reason: str | None = None


class ActionProposalList(PaginatedResponse):
    """Paginated list of action proposals."""

    items: list[ActionProposalRead]


# -------------------------------------------------------
# ActionExecution
# -------------------------------------------------------
class ActionExecutionRead(OrmBase):
    """Read schema for an action execution."""

    execution_id: UUID
    proposal_id: UUID
    executed_by: str
    execution_mode: str
    result_status: str
    result_json: dict[str, Any]
    linked_event_refs: list[Any] = Field(
        default_factory=list,
    )
    trace_id: str
    executed_at: datetime


# -------------------------------------------------------
# ChatMemoryNote
# -------------------------------------------------------
class ChatNoteCreate(OrmBase):
    """Body for creating a memory note."""

    scope_type: str
    scope_key: str
    note_type: str
    content_md: str


class ChatNoteRead(OrmBase):
    """Read schema for a memory note."""

    note_id: UUID
    scope_type: str
    scope_key: str
    note_type: str
    source_session_id: UUID | None = None
    source_message_id: UUID | None = None
    body_md: str
    body_json: dict[str, Any] | None = None
    status: str
    created_by: str
    created_at: datetime


# -------------------------------------------------------
# ModeTransition
# -------------------------------------------------------
class ModeTransitionRequest(OrmBase):
    """Body for requesting a mode transition."""

    target_mode: str
    reason: str | None = None


class ModeTransitionRead(OrmBase):
    """Read schema for a mode transition."""

    transition_id: UUID
    session_id: UUID
    from_mode: str
    to_mode: str
    approved_by: str | None = None
    reason_md: str | None = None
    approved_at: datetime | None = None
    expires_at: datetime | None = None
    trace_id: str
    created_at: datetime


# -------------------------------------------------------
# SessionTimeline (composite read)
# -------------------------------------------------------
class SessionTimelineRead(OrmBase):
    """Full timeline for a chat session."""

    session: ChatSessionRead
    messages: list[ChatMessageRead] = Field(
        default_factory=list,
    )
    intents: list[ChatIntentRead] = Field(
        default_factory=list,
    )
    proposals: list[ActionProposalRead] = Field(
        default_factory=list,
    )
    executions: list[ActionExecutionRead] = (
        Field(default_factory=list)
    )
