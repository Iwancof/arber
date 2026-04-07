"""Ops Chat Copilot service layer.

Covers: session management, context capsule assembly,
message handling, intent extraction, proposal
creation/execution, memory notes, mode transitions.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.outbox import emit_event
from backend.core.trace import get_trace
from backend.models.content import EventLedger
from backend.models.execution import OrderLedger
from backend.models.forecasting import (
    DecisionLedger,
    ForecastLedger,
)
from backend.models.inquiry import InquiryTask
from backend.models.ops import KillSwitch
from backend.models.ops_chat import (
    ChatActionExecution,
    ChatActionProposal,
    ChatIntent,
    ChatMemoryNote,
    ChatMessage,
    ChatModeTransition,
    ChatSession,
    ContextCapsule,
    ContextCapsuleSourceRef,
)
from backend.models.sources import SourceRegistry

# -------------------------------------------------------
# Intent type keywords for v1 extraction
# -------------------------------------------------------
_INTENT_KEYWORDS: dict[str, list[str]] = {
    "query_status": [
        "status", "how is", "what is",
        "overview", "health", "running",
    ],
    "query_symbol": [
        "symbol", "ticker", "stock",
        "dossier", "position",
    ],
    "kill_switch": [
        "kill", "halt", "stop", "freeze",
        "pause",
    ],
    "mode_change": [
        "mode", "switch to", "change to",
        "escalate", "de-escalate",
    ],
    "create_note": [
        "note", "remember", "memo", "save",
    ],
    "query_events": [
        "events", "news", "recent",
        "what happened",
    ],
    "query_forecasts": [
        "forecast", "prediction",
        "probability",
    ],
    "propose_action": [
        "execute", "submit", "create order",
        "place", "do",
    ],
}

# Valid session modes in escalation order
_MODE_ORDER = [
    "observe", "advise", "operate", "implement",
]


# -------------------------------------------------------
# Session management
# -------------------------------------------------------
async def create_session(
    db: AsyncSession,
    *,
    actor_user_id: str,
    session_mode: str,
    scope_entity_type: str | None = None,
    scope_entity_id: str | None = None,
) -> ChatSession:
    """Create a new chat session."""
    trace = get_trace()
    session = ChatSession(
        actor_user_id=actor_user_id,
        session_mode=session_mode,
        active_scope_type=scope_entity_type,
        active_scope_key=scope_entity_id,
        trace_id=trace.trace_id,
        correlation_id=trace.correlation_id,
    )
    db.add(session)
    await db.flush()

    await emit_event(
        db,
        event_type="created",
        aggregate_type="ops_chat.session",
        aggregate_id=str(session.session_id),
        payload={
            "session_mode": session_mode,
            "actor": actor_user_id,
        },
    )
    await db.commit()
    await db.refresh(session)
    return session


async def list_sessions(
    db: AsyncSession,
    *,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ChatSession], int]:
    """List sessions with optional status filter."""
    stmt = select(ChatSession)
    cnt = select(func.count()).select_from(
        ChatSession,
    )
    if status:
        stmt = stmt.where(
            ChatSession.status == status,
        )
        cnt = cnt.where(
            ChatSession.status == status,
        )
    total = (await db.execute(cnt)).scalar_one()
    result = await db.execute(
        stmt.order_by(
            ChatSession.last_activity_at.desc(),
        )
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all(), total


# -------------------------------------------------------
# Context capsule assembly
# -------------------------------------------------------
async def build_global_capsule(
    db: AsyncSession,
) -> ContextCapsule:
    """Build a global status context capsule.

    Queries: execution mode, kill switches,
    active inquiries, recent events count,
    source health, pipeline stats.
    """
    trace = get_trace()
    now = datetime.now(tz=UTC)
    since = now - timedelta(hours=24)

    # Active kill switches
    ks_q = await db.execute(
        select(func.count()).select_from(
            KillSwitch,
        ).where(KillSwitch.active.is_(True))
    )
    active_kill_switches = ks_q.scalar_one()

    # Active inquiry tasks
    active_statuses = [
        "visible", "claimed",
        "awaiting_response", "submitted",
    ]
    inq_q = await db.execute(
        select(func.count()).select_from(
            InquiryTask,
        ).where(
            InquiryTask.task_status.in_(
                active_statuses,
            ),
        )
    )
    active_inquiries = inq_q.scalar_one()

    # Recent events (last 24h)
    evt_q = await db.execute(
        select(func.count()).select_from(
            EventLedger,
        ).where(EventLedger.created_at >= since)
    )
    recent_events_24h = evt_q.scalar_one()

    # Active sources
    src_q = await db.execute(
        select(func.count()).select_from(
            SourceRegistry,
        ).where(SourceRegistry.status == "active")
    )
    active_sources = src_q.scalar_one()

    # Pending decisions
    dec_q = await db.execute(
        select(func.count()).select_from(
            DecisionLedger,
        ).where(
            DecisionLedger.decision_status.in_([
                "candidate", "waiting_manual",
            ]),
        )
    )
    pending_decisions = dec_q.scalar_one()

    # Recent orders (last 24h)
    ord_q = await db.execute(
        select(func.count()).select_from(
            OrderLedger,
        ).where(
            OrderLedger.submitted_at >= since,
        )
    )
    recent_orders_24h = ord_q.scalar_one()

    summary_json: dict[str, Any] = {
        "active_kill_switches": (
            active_kill_switches
        ),
        "active_inquiries": active_inquiries,
        "recent_events_24h": recent_events_24h,
        "active_sources": active_sources,
        "pending_decisions": pending_decisions,
        "recent_orders_24h": recent_orders_24h,
        "generated_at": now.isoformat(),
    }

    ks_label = (
        "ACTIVE" if active_kill_switches > 0
        else "none"
    )
    summary_md = (
        f"## Global Status\n"
        f"- Kill switches: {ks_label} "
        f"({active_kill_switches})\n"
        f"- Active inquiries: "
        f"{active_inquiries}\n"
        f"- Events (24h): "
        f"{recent_events_24h}\n"
        f"- Active sources: {active_sources}\n"
        f"- Pending decisions: "
        f"{pending_decisions}\n"
        f"- Orders (24h): "
        f"{recent_orders_24h}\n"
    )

    capsule = ContextCapsule(
        capsule_type="global_status",
        scope_key="global",
        fresh_until=now + timedelta(minutes=5),
        summary_md=summary_md,
        summary_json=summary_json,
        evidence_refs=[],
        trace_id=trace.trace_id,
        created_by="capsule_assembler",
    )
    db.add(capsule)
    await db.flush()

    await emit_event(
        db,
        event_type="created",
        aggregate_type=(
            "ops_chat.context_capsule"
        ),
        aggregate_id=str(capsule.capsule_id),
        payload={
            "capsule_type": "global_status",
            "scope_key": "global",
        },
    )
    await db.commit()
    await db.refresh(capsule)
    return capsule


async def build_symbol_capsule(
    db: AsyncSession,
    *,
    symbol: str,
) -> ContextCapsule:
    """Build a symbol dossier context capsule.

    Queries: instrument, recent events,
    forecasts, decisions, orders for that symbol.
    """
    trace = get_trace()
    now = datetime.now(tz=UTC)
    since = now - timedelta(days=7)

    # Find instrument by symbol
    from backend.models.core import Instrument
    inst_q = await db.execute(
        select(Instrument).where(
            Instrument.symbol == symbol,
        )
    )
    inst = inst_q.scalar_one_or_none()
    inst_id = inst.instrument_id if inst else None
    inst_name = (
        inst.display_name if inst else symbol
    )

    events_count = 0
    forecasts_count = 0
    decisions_count = 0
    orders_count = 0
    latest_forecast_json: dict[str, Any] = {}

    if inst_id is not None:
        # Events for symbol (via asset impact)
        from backend.models.content import (
            EventAssetImpact,
        )
        evt_q = await db.execute(
            select(func.count()).select_from(
                EventAssetImpact,
            ).where(
                EventAssetImpact.instrument_id
                == inst_id,
            )
        )
        events_count = evt_q.scalar_one()

        # Forecasts
        fc_q = await db.execute(
            select(func.count()).select_from(
                ForecastLedger,
            ).where(
                ForecastLedger.instrument_id
                == inst_id,
                ForecastLedger.forecasted_at
                >= since,
            )
        )
        forecasts_count = fc_q.scalar_one()

        # Latest forecast
        latest_fc = await db.execute(
            select(ForecastLedger).where(
                ForecastLedger.instrument_id
                == inst_id,
            ).order_by(
                ForecastLedger.forecasted_at.desc(),
            ).limit(1)
        )
        lf = latest_fc.scalar_one_or_none()
        if lf is not None:
            latest_forecast_json = {
                "forecast_id": str(lf.forecast_id),
                "confidence": (
                    str(lf.confidence)
                    if lf.confidence else None
                ),
                "mode": lf.forecast_mode,
                "at": (
                    lf.forecasted_at.isoformat()
                ),
            }

        # Decisions linked via forecast
        dc_q = await db.execute(
            select(func.count())
            .select_from(DecisionLedger)
            .join(
                ForecastLedger,
                DecisionLedger.forecast_id
                == ForecastLedger.forecast_id,
            )
            .where(
                ForecastLedger.instrument_id
                == inst_id,
                DecisionLedger.decided_at >= since,
            )
        )
        decisions_count = dc_q.scalar_one()

        # Orders
        ord_q = await db.execute(
            select(func.count()).select_from(
                OrderLedger,
            ).where(
                OrderLedger.instrument_id == inst_id,
                OrderLedger.submitted_at >= since,
            )
        )
        orders_count = ord_q.scalar_one()

    summary_json: dict[str, Any] = {
        "symbol": symbol,
        "instrument_name": inst_name,
        "instrument_id": (
            str(inst_id) if inst_id else None
        ),
        "events_count": events_count,
        "forecasts_7d": forecasts_count,
        "decisions_7d": decisions_count,
        "orders_7d": orders_count,
        "latest_forecast": latest_forecast_json,
        "generated_at": now.isoformat(),
    }

    found = "Found" if inst_id else "Not found"
    summary_md = (
        f"## Symbol Dossier: {symbol}\n"
        f"- Instrument: {found} "
        f"({inst_name})\n"
        f"- Events (all): {events_count}\n"
        f"- Forecasts (7d): "
        f"{forecasts_count}\n"
        f"- Decisions (7d): "
        f"{decisions_count}\n"
        f"- Orders (7d): {orders_count}\n"
    )

    capsule = ContextCapsule(
        capsule_type="symbol_dossier",
        scope_key=symbol,
        fresh_until=now + timedelta(minutes=5),
        summary_md=summary_md,
        summary_json=summary_json,
        evidence_refs=[],
        trace_id=trace.trace_id,
        created_by="capsule_assembler",
    )
    db.add(capsule)
    await db.flush()

    # Add source refs if instrument found
    if inst_id is not None:
        ref = ContextCapsuleSourceRef(
            capsule_id=capsule.capsule_id,
            ref_kind="instrument",
            ref_id=str(inst_id),
        )
        db.add(ref)

    await emit_event(
        db,
        event_type="created",
        aggregate_type=(
            "ops_chat.context_capsule"
        ),
        aggregate_id=str(capsule.capsule_id),
        payload={
            "capsule_type": "symbol_dossier",
            "scope_key": symbol,
        },
    )
    await db.commit()
    await db.refresh(capsule)
    return capsule


# -------------------------------------------------------
# Message handling
# -------------------------------------------------------
async def append_message(
    db: AsyncSession,
    *,
    session_id: UUID,
    role: str,
    content_md: str,
) -> ChatMessage:
    """Append a message to a session."""
    msg = ChatMessage(
        session_id=session_id,
        role=role,
        content_md=content_md,
    )
    db.add(msg)

    # Update session last_activity_at
    sess_q = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
        )
    )
    sess = sess_q.scalar_one()
    sess.last_activity_at = datetime.now(tz=UTC)

    await db.flush()
    await db.commit()
    await db.refresh(msg)
    return msg


# -------------------------------------------------------
# Intent extraction (v1: keyword matching)
# -------------------------------------------------------
async def extract_intent(
    db: AsyncSession,
    *,
    session_id: UUID,
    message_id: UUID,
    user_text: str,
) -> ChatIntent:
    """Extract intent from user text.

    V1 implementation uses keyword matching.
    Future versions will call LLM via
    AnthropicWorkerAdapter.
    """
    lower = user_text.lower()
    best_type = "query_status"
    best_score = Decimal("0.3")
    scope_json: dict[str, Any] = {}

    for itype, keywords in _INTENT_KEYWORDS.items():
        hits = sum(
            1 for kw in keywords if kw in lower
        )
        if hits > 0:
            score = Decimal(str(
                min(0.5 + hits * 0.15, 0.95)
            ))
            if score > best_score:
                best_score = score
                best_type = itype

    # Extract symbol hint from text
    words = user_text.split()
    for w in words:
        cleaned = w.strip("?.,!").upper()
        if (
            len(cleaned) >= 1
            and len(cleaned) <= 6
            and cleaned.isalpha()
            and cleaned == cleaned.upper()
            and cleaned not in {
                "I", "A", "THE", "IS", "IT",
                "AND", "OR", "TO", "IN", "FOR",
                "MY", "DO", "HOW", "WHAT", "CAN",
            }
        ):
            scope_json["symbol_hint"] = cleaned
            break

    risk_hints = {
        "kill_switch": "high",
        "mode_change": "medium",
        "propose_action": "high",
        "create_note": "low",
        "query_status": "low",
        "query_symbol": "low",
        "query_events": "low",
        "query_forecasts": "low",
    }

    intent = ChatIntent(
        session_id=session_id,
        source_message_id=message_id,
        intent_type=best_type,
        confidence=best_score,
        intent_json={
            "scope": scope_json,
            "risk_hint": risk_hints.get(
                best_type, "low"
            ),
            "raw_text_length": len(user_text),
        },
        status="parsed",
    )
    db.add(intent)
    await db.flush()

    await emit_event(
        db,
        event_type="parsed",
        aggregate_type="ops_chat.intent",
        aggregate_id=str(intent.intent_id),
        payload={
            "intent_type": best_type,
            "confidence": str(best_score),
            "session_id": str(session_id),
        },
    )
    await db.commit()
    await db.refresh(intent)
    return intent


# -------------------------------------------------------
# Proposal creation
# -------------------------------------------------------
async def create_proposal(
    db: AsyncSession,
    *,
    intent_id: UUID,
    summary_md: str,
    diff_json: dict[str, Any] | None = None,
    command_json: dict[str, Any] | None = None,
    risk_tier: str = "medium",
    requires_confirmation: bool = True,
) -> ChatActionProposal:
    """Create an action proposal from an intent."""
    proposal = ChatActionProposal(
        intent_id=intent_id,
        proposal_type="chat_action",
        risk_tier=risk_tier,
        requires_confirmation=requires_confirmation,
        summary_md=summary_md,
        diff_json=diff_json,
        command_json=command_json or {},
        blocked_by=[],
        status="pending",
    )
    db.add(proposal)
    await db.flush()

    await emit_event(
        db,
        event_type="created",
        aggregate_type="ops_chat.proposal",
        aggregate_id=str(proposal.proposal_id),
        payload={
            "intent_id": str(intent_id),
            "risk_tier": risk_tier,
        },
    )
    await db.commit()
    await db.refresh(proposal)
    return proposal


# -------------------------------------------------------
# Proposal execution
# -------------------------------------------------------
async def confirm_proposal(
    db: AsyncSession,
    *,
    proposal_id: UUID,
) -> ChatActionExecution:
    """Confirm and execute a pending proposal."""
    trace = get_trace()

    p_q = await db.execute(
        select(ChatActionProposal).where(
            ChatActionProposal.proposal_id
            == proposal_id,
        )
    )
    proposal = p_q.scalar_one()

    if proposal.status != "pending":
        msg = (
            f"Cannot confirm proposal in "
            f"'{proposal.status}' status"
        )
        raise ValueError(msg)

    now = datetime.now(tz=UTC)
    proposal.status = "confirmed"
    proposal.confirmed_at = now
    proposal.confirmed_by = "operator"

    execution = ChatActionExecution(
        proposal_id=proposal_id,
        executed_by="ops_chat_service",
        execution_mode="paper",
        result_status="success",
        result_json={
            "confirmed_at": now.isoformat(),
            "command": proposal.command_json,
        },
        linked_event_refs=[],
        trace_id=trace.trace_id,
    )
    db.add(execution)
    await db.flush()

    proposal.status = "executed"

    await emit_event(
        db,
        event_type="confirmed",
        aggregate_type="ops_chat.proposal",
        aggregate_id=str(proposal_id),
        payload={
            "execution_id": str(
                execution.execution_id,
            ),
        },
    )
    await emit_event(
        db,
        event_type="completed",
        aggregate_type="ops_chat.execution",
        aggregate_id=str(
            execution.execution_id,
        ),
        payload={
            "proposal_id": str(proposal_id),
            "result_status": "success",
        },
    )
    await db.commit()
    await db.refresh(execution)
    return execution


async def reject_proposal(
    db: AsyncSession,
    *,
    proposal_id: UUID,
    reason: str | None = None,
) -> ChatActionProposal:
    """Reject a pending proposal."""
    p_q = await db.execute(
        select(ChatActionProposal).where(
            ChatActionProposal.proposal_id
            == proposal_id,
        )
    )
    proposal = p_q.scalar_one()

    if proposal.status != "pending":
        msg = (
            f"Cannot reject proposal in "
            f"'{proposal.status}' status"
        )
        raise ValueError(msg)

    proposal.status = "rejected"

    await emit_event(
        db,
        event_type="rejected",
        aggregate_type="ops_chat.proposal",
        aggregate_id=str(proposal_id),
        payload={
            "reason": reason or "",
        },
    )
    await db.commit()
    await db.refresh(proposal)
    return proposal


# -------------------------------------------------------
# Notes
# -------------------------------------------------------
async def create_note(
    db: AsyncSession,
    *,
    scope_type: str,
    scope_key: str,
    note_type: str,
    content_md: str,
    source_session_id: UUID | None = None,
) -> ChatMemoryNote:
    """Create a chat-promoted memory note."""
    note = ChatMemoryNote(
        scope_type=scope_type,
        scope_key=scope_key,
        note_type=note_type,
        source_session_id=source_session_id,
        body_md=content_md,
        status="active",
        created_by="ops_chat_service",
    )
    db.add(note)
    await db.flush()

    await emit_event(
        db,
        event_type="created",
        aggregate_type="ops_chat.note",
        aggregate_id=str(note.note_id),
        payload={
            "scope_type": scope_type,
            "scope_key": scope_key,
            "note_type": note_type,
        },
    )
    await db.commit()
    await db.refresh(note)
    return note


# -------------------------------------------------------
# Mode transition
# -------------------------------------------------------
async def transition_mode(
    db: AsyncSession,
    *,
    session_id: UUID,
    target_mode: str,
    approved_by: str | None = None,
    reason: str | None = None,
    expires_at: datetime | None = None,
) -> ChatModeTransition:
    """Transition a session to a new mode."""
    trace = get_trace()

    if target_mode not in _MODE_ORDER:
        msg = f"Invalid target mode: {target_mode}"
        raise ValueError(msg)

    sess_q = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
        )
    )
    session = sess_q.scalar_one()

    from_mode = session.session_mode
    if from_mode == target_mode:
        msg = f"Already in mode '{target_mode}'"
        raise ValueError(msg)

    transition = ChatModeTransition(
        session_id=session_id,
        from_mode=from_mode,
        to_mode=target_mode,
        approved_by=approved_by,
        reason_md=reason,
        approved_at=datetime.now(tz=UTC),
        expires_at=expires_at,
        trace_id=trace.trace_id,
    )
    db.add(transition)

    session.session_mode = target_mode
    session.last_activity_at = datetime.now(
        tz=UTC,
    )

    await db.flush()

    await emit_event(
        db,
        event_type="mode_changed",
        aggregate_type="ops_chat.session",
        aggregate_id=str(session_id),
        payload={
            "from_mode": from_mode,
            "to_mode": target_mode,
            "reason": reason or "",
        },
    )
    await db.commit()
    await db.refresh(transition)
    return transition
