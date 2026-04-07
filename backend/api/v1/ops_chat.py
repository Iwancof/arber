"""Ops Chat Copilot API endpoints.

Endpoints:
  POST   /ops-chat/sessions
  GET    /ops-chat/sessions
  GET    /ops-chat/sessions/{id}/timeline
  POST   /ops-chat/sessions/{id}/messages
  GET    /ops-chat/context/global
  GET    /ops-chat/context/symbols/{symbol}
  GET    /ops-chat/proposals
  POST   /ops-chat/proposals/{id}/confirm
  POST   /ops-chat/proposals/{id}/reject
  POST   /ops-chat/notes
  POST   /ops-chat/mode/{session_id}
"""

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.models.ops_chat import (
    ChatActionExecution,
    ChatActionProposal,
    ChatIntent,
    ChatMessage,
    ChatSession,
)
from backend.schemas.ops_chat import (
    ActionExecutionRead,
    ActionProposalConfirm,
    ActionProposalList,
    ActionProposalRead,
    ActionProposalReject,
    ChatIntentRead,
    ChatMessageCreate,
    ChatMessageRead,
    ChatNoteCreate,
    ChatNoteRead,
    ChatSessionCreate,
    ChatSessionList,
    ChatSessionRead,
    ContextCapsuleRead,
    ModeTransitionRead,
    ModeTransitionRequest,
    SessionTimelineRead,
)
from backend.services.ops_chat import (
    append_message,
    build_global_capsule,
    build_symbol_capsule,
    confirm_proposal,
    create_note,
    create_session,
    extract_intent,
    list_sessions,
    reject_proposal,
    transition_mode,
)

router = APIRouter(
    prefix="/ops-chat",
    tags=["ops-chat"],
)

# Placeholder user ID; in production this comes
# from auth middleware.
_PLACEHOLDER_USER = "system-operator"


# -------------------------------------------------------
# Sessions
# -------------------------------------------------------
@router.post(
    "/sessions",
    response_model=ChatSessionRead,
    status_code=201,
    summary="Create chat session",
)
async def create_session_endpoint(
    body: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
) -> ChatSessionRead:
    """Create a new ops chat session."""
    session = await create_session(
        db,
        actor_user_id=_PLACEHOLDER_USER,
        session_mode=body.session_mode,
        scope_entity_type=(
            body.scope_entity_type
        ),
        scope_entity_id=body.scope_entity_id,
    )
    return _session_to_read(session)


@router.get(
    "/sessions",
    response_model=ChatSessionList,
    summary="List chat sessions",
)
async def list_sessions_endpoint(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionList:
    """List ops chat sessions."""
    sessions, total = await list_sessions(
        db,
        status=status,
        limit=limit,
        offset=offset,
    )
    items = [
        _session_to_read(s) for s in sessions
    ]
    return ChatSessionList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/sessions/{session_id}/timeline",
    response_model=SessionTimelineRead,
    summary="Get session timeline",
)
async def get_session_timeline(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SessionTimelineRead:
    """Get full timeline with messages,
    intents, proposals, and executions."""
    sess_q = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
        )
    )
    session = sess_q.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    # Messages
    msg_q = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.session_id == session_id,
        )
        .order_by(ChatMessage.created_at.asc())
    )
    messages = [
        _message_to_read(m)
        for m in msg_q.scalars().all()
    ]

    # Intents
    int_q = await db.execute(
        select(ChatIntent)
        .where(
            ChatIntent.session_id == session_id,
        )
        .order_by(ChatIntent.created_at.asc())
    )
    intents_list = int_q.scalars().all()
    intents = [
        _intent_to_read(i) for i in intents_list
    ]

    # Proposals (via intents)
    intent_ids = [
        i.intent_id for i in intents_list
    ]
    proposals: list[ActionProposalRead] = []
    executions: list[ActionExecutionRead] = []

    if intent_ids:
        prop_q = await db.execute(
            select(ChatActionProposal)
            .where(
                ChatActionProposal.intent_id.in_(
                    intent_ids,
                ),
            )
            .order_by(
                ChatActionProposal.created_at.asc()
            )
        )
        props = prop_q.scalars().all()
        proposals = [
            _proposal_to_read(p) for p in props
        ]

        prop_ids = [
            p.proposal_id for p in props
        ]
        if prop_ids:
            exec_q = await db.execute(
                select(ChatActionExecution)
                .where(
                    ChatActionExecution
                    .proposal_id.in_(prop_ids),
                )
                .order_by(
                    ChatActionExecution
                    .executed_at.asc()
                )
            )
            executions = [
                _execution_to_read(e)
                for e in exec_q.scalars().all()
            ]

    return SessionTimelineRead(
        session=_session_to_read(session),
        messages=messages,
        intents=intents,
        proposals=proposals,
        executions=executions,
    )


# -------------------------------------------------------
# Messages
# -------------------------------------------------------
@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatMessageRead,
    status_code=202,
    summary="Append message and trigger intent",
)
async def append_message_endpoint(
    session_id: UUID,
    body: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
) -> ChatMessageRead:
    """Append a user message and trigger
    intent extraction (202 Accepted)."""
    # Verify session exists
    sess_q = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
        )
    )
    session = sess_q.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )
    if session.status == "closed":
        raise HTTPException(
            status_code=409,
            detail="Session is closed",
        )

    msg = await append_message(
        db,
        session_id=session_id,
        role="user",
        content_md=body.content_md,
    )

    # Trigger intent extraction (inline v1)
    await extract_intent(
        db,
        session_id=session_id,
        message_id=msg.message_id,
        user_text=body.content_md,
    )

    return _message_to_read(msg)


# -------------------------------------------------------
# Context Capsules
# -------------------------------------------------------
@router.get(
    "/context/global",
    response_model=ContextCapsuleRead,
    summary="Get global status capsule",
)
async def get_global_capsule(
    db: AsyncSession = Depends(get_db),
) -> ContextCapsuleRead:
    """Get current global status capsule."""
    capsule = await build_global_capsule(db)
    return _capsule_to_read(capsule)


@router.get(
    "/context/symbols/{symbol}",
    response_model=ContextCapsuleRead,
    summary="Get symbol dossier capsule",
)
async def get_symbol_capsule(
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> ContextCapsuleRead:
    """Get symbol dossier context capsule."""
    capsule = await build_symbol_capsule(
        db, symbol=symbol,
    )
    return _capsule_to_read(capsule)


# -------------------------------------------------------
# Proposals
# -------------------------------------------------------
@router.get(
    "/proposals",
    response_model=ActionProposalList,
    summary="List pending proposals",
)
async def list_proposals_endpoint(
    status: str | None = Query(
        default="pending",
    ),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ActionProposalList:
    """List action proposals, default pending."""
    stmt = select(ChatActionProposal)
    cnt = select(func.count()).select_from(
        ChatActionProposal,
    )
    if status:
        stmt = stmt.where(
            ChatActionProposal.status == status,
        )
        cnt = cnt.where(
            ChatActionProposal.status == status,
        )
    total = (await db.execute(cnt)).scalar_one()
    result = await db.execute(
        stmt.order_by(
            ChatActionProposal.created_at.desc(),
        )
        .offset(offset)
        .limit(limit)
    )
    items = [
        _proposal_to_read(p)
        for p in result.scalars().all()
    ]
    return ActionProposalList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/proposals/{proposal_id}/confirm",
    response_model=ActionExecutionRead,
    summary="Confirm proposal",
)
async def confirm_proposal_endpoint(
    proposal_id: UUID,
    body: ActionProposalConfirm | None = None,
    db: AsyncSession = Depends(get_db),
) -> ActionExecutionRead:
    """Confirm and execute a proposal."""
    try:
        execution = await confirm_proposal(
            db, proposal_id=proposal_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=409, detail=str(e),
        ) from e
    return _execution_to_read(execution)


@router.post(
    "/proposals/{proposal_id}/reject",
    response_model=ActionProposalRead,
    summary="Reject proposal",
)
async def reject_proposal_endpoint(
    proposal_id: UUID,
    body: ActionProposalReject | None = None,
    db: AsyncSession = Depends(get_db),
) -> ActionProposalRead:
    """Reject a pending proposal."""
    reason = body.reason if body else None
    try:
        proposal = await reject_proposal(
            db,
            proposal_id=proposal_id,
            reason=reason,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=409, detail=str(e),
        ) from e
    return _proposal_to_read(proposal)


# -------------------------------------------------------
# Notes
# -------------------------------------------------------
@router.post(
    "/notes",
    response_model=ChatNoteRead,
    status_code=201,
    summary="Create memory note",
)
async def create_note_endpoint(
    body: ChatNoteCreate,
    db: AsyncSession = Depends(get_db),
) -> ChatNoteRead:
    """Create a chat-promoted memory note."""
    note = await create_note(
        db,
        scope_type=body.scope_type,
        scope_key=body.scope_key,
        note_type=body.note_type,
        content_md=body.content_md,
    )
    return ChatNoteRead(
        note_id=note.note_id,
        scope_type=note.scope_type,
        scope_key=note.scope_key,
        note_type=note.note_type,
        source_session_id=(
            note.source_session_id
        ),
        source_message_id=(
            note.source_message_id
        ),
        body_md=note.body_md,
        body_json=note.body_json,
        status=note.status,
        created_by=note.created_by,
        created_at=note.created_at,
    )


# -------------------------------------------------------
# Mode transition
# -------------------------------------------------------
@router.post(
    "/mode/{session_id}",
    response_model=ModeTransitionRead,
    summary="Change session mode",
)
async def mode_transition_endpoint(
    session_id: UUID,
    body: ModeTransitionRequest,
    db: AsyncSession = Depends(get_db),
) -> ModeTransitionRead:
    """Change a chat session's mode."""
    try:
        transition = await transition_mode(
            db,
            session_id=session_id,
            target_mode=body.target_mode,
            approved_by=_PLACEHOLDER_USER,
            reason=body.reason,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=409, detail=str(e),
        ) from e
    return ModeTransitionRead(
        transition_id=transition.transition_id,
        session_id=transition.session_id,
        from_mode=transition.from_mode,
        to_mode=transition.to_mode,
        approved_by=transition.approved_by,
        reason_md=transition.reason_md,
        approved_at=transition.approved_at,
        expires_at=transition.expires_at,
        trace_id=transition.trace_id,
        created_at=transition.created_at,
    )


# -------------------------------------------------------
# Internal read helpers
# -------------------------------------------------------
def _session_to_read(
    s: ChatSession,
) -> ChatSessionRead:
    """Convert ORM session to read schema."""
    return ChatSessionRead(
        session_id=s.session_id,
        channel=s.channel,
        actor_user_id=s.actor_user_id,
        actor_display_name=(
            s.actor_display_name
        ),
        session_mode=s.session_mode,
        title=s.title,
        active_scope_type=s.active_scope_type,
        active_scope_key=s.active_scope_key,
        trace_id=s.trace_id,
        correlation_id=s.correlation_id,
        started_at=s.started_at,
        last_activity_at=s.last_activity_at,
        closed_at=s.closed_at,
        status=s.status,
    )


def _message_to_read(
    m: ChatMessage,
) -> ChatMessageRead:
    """Convert ORM message to read schema."""
    return ChatMessageRead(
        message_id=m.message_id,
        session_id=m.session_id,
        role=m.role,
        content_md=m.content_md,
        content_json=m.content_json,
        provenance_json=m.provenance_json,
        created_at=m.created_at,
    )


def _intent_to_read(
    i: ChatIntent,
) -> ChatIntentRead:
    """Convert ORM intent to read schema."""
    return ChatIntentRead(
        intent_id=i.intent_id,
        session_id=i.session_id,
        source_message_id=i.source_message_id,
        intent_type=i.intent_type,
        confidence=i.confidence,
        intent_json=i.intent_json,
        status=i.status,
        created_at=i.created_at,
    )


def _proposal_to_read(
    p: ChatActionProposal,
) -> ActionProposalRead:
    """Convert ORM proposal to read schema."""
    return ActionProposalRead(
        proposal_id=p.proposal_id,
        intent_id=p.intent_id,
        proposal_type=p.proposal_type,
        risk_tier=p.risk_tier,
        requires_confirmation=(
            p.requires_confirmation
        ),
        expires_at=p.expires_at,
        summary_md=p.summary_md,
        diff_json=p.diff_json,
        command_json=p.command_json,
        blocked_by=p.blocked_by,
        status=p.status,
        created_at=p.created_at,
        confirmed_at=p.confirmed_at,
        confirmed_by=p.confirmed_by,
    )


def _execution_to_read(
    e: ChatActionExecution,
) -> ActionExecutionRead:
    """Convert ORM execution to read schema."""
    return ActionExecutionRead(
        execution_id=e.execution_id,
        proposal_id=e.proposal_id,
        executed_by=e.executed_by,
        execution_mode=e.execution_mode,
        result_status=e.result_status,
        result_json=e.result_json,
        linked_event_refs=e.linked_event_refs,
        trace_id=e.trace_id,
        executed_at=e.executed_at,
    )


def _capsule_to_read(capsule) -> ContextCapsuleRead:
    """Convert ORM capsule to read schema."""
    return ContextCapsuleRead(
        capsule_id=capsule.capsule_id,
        capsule_type=capsule.capsule_type,
        scope_key=capsule.scope_key,
        generated_at=capsule.generated_at,
        fresh_until=capsule.fresh_until,
        status=capsule.status,
        summary_md=capsule.summary_md,
        summary_json=capsule.summary_json,
        evidence_refs=capsule.evidence_refs,
        trace_id=capsule.trace_id,
        created_by=capsule.created_by,
    )
