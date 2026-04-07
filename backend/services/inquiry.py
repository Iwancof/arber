"""Human Inquiry Orchestration service layer.

Manages the full lifecycle of inquiry cases, tasks,
responses, and resolutions.

State machines
--------------
Case:  open -> monitoring -> resolved | canceled
Task:  draft -> visible -> claimed -> awaiting_response
       -> submitted -> parsed -> accepted | rejected
       | expired | superseded | canceled
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.outbox import emit_event
from backend.models.inquiry import (
    InquiryAssignment,
    InquiryCase,
    InquiryPresence,
    InquiryResolution,
    InquiryResponse,
    InquiryTask,
)

# ---------------------------------------------------------------
# Valid state transitions
# ---------------------------------------------------------------
_CASE_TRANSITIONS: dict[str, list[str]] = {
    "open": ["monitoring", "resolved", "canceled"],
    "monitoring": ["resolved", "canceled"],
}

_TASK_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["visible", "canceled"],
    "visible": [
        "claimed",
        "expired",
        "superseded",
        "canceled",
    ],
    "claimed": [
        "awaiting_response",
        "visible",
        "expired",
        "superseded",
        "canceled",
    ],
    "awaiting_response": [
        "submitted",
        "expired",
        "superseded",
        "canceled",
    ],
    "submitted": [
        "parsed",
        "expired",
        "superseded",
    ],
    "parsed": [
        "accepted",
        "rejected",
        "superseded",
    ],
}


def _assert_task_transition(
    current: str,
    target: str,
) -> None:
    """Raise ValueError when a transition is invalid."""
    allowed = _TASK_TRANSITIONS.get(current, [])
    if target not in allowed:
        msg = (
            f"Cannot transition task from "
            f"'{current}' to '{target}'"
        )
        raise ValueError(msg)


# ---------------------------------------------------------------
# Case helpers
# ---------------------------------------------------------------
async def create_inquiry_case(
    db: AsyncSession,
    *,
    market_profile_code: str,
    linked_entity_type: str,
    linked_entity_id: UUID | None,
    inquiry_kind: str,
    dedupe_key: str,
    title: str,
    benchmark_symbol: str | None = None,
    primary_symbol: str | None = None,
    horizon_code: str | None = None,
    urgency_class: str = "normal",
    metadata_json: dict[str, Any] | None = None,
) -> InquiryCase:
    """Create an inquiry case with dedup check.

    If a case with the same (market_profile_code,
    inquiry_kind, dedupe_key) already exists in
    ``open`` or ``monitoring`` status, return it
    instead of creating a duplicate.
    """
    existing = await db.execute(
        select(InquiryCase).where(
            InquiryCase.market_profile_code
            == market_profile_code,
            InquiryCase.inquiry_kind
            == inquiry_kind,
            InquiryCase.dedupe_key == dedupe_key,
            InquiryCase.case_status.in_(
                ["open", "monitoring"]
            ),
        )
    )
    found = existing.scalar_one_or_none()
    if found is not None:
        return found

    case = InquiryCase(
        market_profile_code=market_profile_code,
        linked_entity_type=linked_entity_type,
        linked_entity_id=linked_entity_id,
        inquiry_kind=inquiry_kind,
        dedupe_key=dedupe_key,
        title=title,
        benchmark_symbol=benchmark_symbol,
        primary_symbol=primary_symbol,
        horizon_code=horizon_code,
        urgency_class=urgency_class,
        case_status="open",
        metadata_json=metadata_json or {},
    )
    db.add(case)
    await db.flush()

    await emit_event(
        db,
        event_type="created",
        aggregate_type="inquiry_case",
        aggregate_id=str(case.inquiry_case_id),
        payload={
            "inquiry_kind": inquiry_kind,
            "market_profile_code": market_profile_code,
            "dedupe_key": dedupe_key,
        },
    )
    await db.commit()
    await db.refresh(case)
    return case


# ---------------------------------------------------------------
# Task helpers
# ---------------------------------------------------------------
async def _next_revision_no(
    db: AsyncSession,
    case_id: UUID,
) -> int:
    """Return max(revision_no)+1 for a case."""
    result = await db.execute(
        select(
            func.coalesce(
                func.max(InquiryTask.revision_no),
                0,
            )
        ).where(
            InquiryTask.inquiry_case_id == case_id,
        )
    )
    return int(result.scalar_one()) + 1


async def spawn_inquiry_task(
    db: AsyncSession,
    *,
    case_id: UUID,
    question_title: str,
    question_text: str,
    deadline_at: datetime,
    sla_class: str = "normal",
    bounded_evidence_json: (
        list[Any] | None
    ) = None,
    acceptance_rules_json: (
        list[str] | None
    ) = None,
    required_schema_name: str = (
        "inquiry_response"
    ),
    required_schema_version: str = "1.0.0",
) -> InquiryTask:
    """Spawn a new task for a case.

    If an active task (draft/visible/claimed/
    awaiting_response) exists on the same case,
    supersede it first.
    """
    # Supersede any active sibling tasks
    active_statuses = [
        "draft",
        "visible",
        "claimed",
        "awaiting_response",
    ]
    active_q = await db.execute(
        select(InquiryTask).where(
            InquiryTask.inquiry_case_id == case_id,
            InquiryTask.task_status.in_(
                active_statuses
            ),
        )
    )
    for old_task in active_q.scalars().all():
        old_task.task_status = "superseded"
        old_task.updated_at = datetime.now(
            tz=UTC,
        )

    rev = await _next_revision_no(db, case_id)
    task = InquiryTask(
        inquiry_case_id=case_id,
        revision_no=rev,
        question_title=question_title,
        question_text=question_text,
        deadline_at=deadline_at,
        sla_class=sla_class,
        task_status="visible",
        bounded_evidence_json=(
            bounded_evidence_json or []
        ),
        acceptance_rules_json=(
            acceptance_rules_json or []
        ),
        required_schema_name=required_schema_name,
        required_schema_version=(
            required_schema_version
        ),
    )
    db.add(task)
    await db.flush()

    await emit_event(
        db,
        event_type="created",
        aggregate_type="inquiry_task",
        aggregate_id=str(task.inquiry_task_id),
        payload={
            "case_id": str(case_id),
            "revision_no": rev,
            "sla_class": sla_class,
        },
    )
    await db.commit()
    await db.refresh(task)
    return task


async def claim_task(
    db: AsyncSession,
    *,
    task_id: UUID,
    user_id: UUID,
) -> InquiryTask:
    """Claim a visible task for an operator."""
    result = await db.execute(
        select(InquiryTask).where(
            InquiryTask.inquiry_task_id == task_id,
        )
    )
    task = result.scalar_one()
    _assert_task_transition(
        task.task_status, "claimed",
    )
    task.task_status = "claimed"
    task.updated_at = datetime.now(tz=UTC)

    # Record assignment
    assignment = InquiryAssignment(
        inquiry_task_id=task_id,
        assigned_user_id=user_id,
        assignment_mode="exclusive",
        assignment_status="claimed",
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(task)
    return task


async def snooze_task(
    db: AsyncSession,
    *,
    task_id: UUID,
    snooze_until: datetime,
) -> InquiryTask:
    """Snooze a task until a given time.

    The task stays in its current status but is
    hidden from the tray until snooze_until.
    """
    result = await db.execute(
        select(InquiryTask).where(
            InquiryTask.inquiry_task_id == task_id,
        )
    )
    task = result.scalar_one()
    if task.task_status in (
        "accepted",
        "rejected",
        "expired",
        "superseded",
        "canceled",
    ):
        msg = (
            f"Cannot snooze task in "
            f"'{task.task_status}' status"
        )
        raise ValueError(msg)

    # Use claim_expires_at as snooze marker
    task.claim_expires_at = snooze_until
    task.updated_at = datetime.now(tz=UTC)
    await db.commit()
    await db.refresh(task)
    return task


async def submit_inquiry_response(
    db: AsyncSession,
    *,
    task_id: UUID,
    response_channel: str,
    raw_response: str,
    model_name_user_entered: str | None = None,
    notes: str | None = None,
    submitted_by: UUID | None = None,
) -> InquiryResponse:
    """Submit a response to an inquiry task.

    Transitions the task to ``submitted``.
    """
    task_result = await db.execute(
        select(InquiryTask).where(
            InquiryTask.inquiry_task_id == task_id,
        )
    )
    task = task_result.scalar_one()

    submittable = (
        "claimed",
        "awaiting_response",
        "visible",
    )
    if task.task_status not in submittable:
        msg = (
            "Cannot submit response: task status "
            f"is '{task.task_status}'"
        )
        raise ValueError(msg)

    # Check if response is late
    now = datetime.now(tz=UTC)
    is_late = (
        task.deadline_at is not None
        and now > task.deadline_at
    )

    response = InquiryResponse(
        inquiry_task_id=task_id,
        response_channel=response_channel,
        model_name_user_entered=(
            model_name_user_entered
        ),
        raw_response=raw_response,
        notes=notes,
        submitted_by=submitted_by,
        response_status=(
            "late" if is_late else "received"
        ),
    )
    db.add(response)
    task.task_status = "submitted"
    task.updated_at = now

    await db.flush()
    await emit_event(
        db,
        event_type="received",
        aggregate_type="inquiry_response",
        aggregate_id=str(
            response.inquiry_response_id,
        ),
        payload={
            "task_id": str(task_id),
            "channel": response_channel,
            "is_late": is_late,
        },
    )
    await db.commit()
    await db.refresh(response)
    return response


async def accept_inquiry_response(
    db: AsyncSession,
    *,
    task_id: UUID,
    response_id: UUID,
    weight: Decimal = Decimal("1.0"),
) -> InquiryResolution:
    """Accept a response and create a resolution.

    Transitions the task to ``accepted``.
    """
    task_result = await db.execute(
        select(InquiryTask).where(
            InquiryTask.inquiry_task_id == task_id,
        )
    )
    task = task_result.scalar_one()
    _assert_task_transition(
        task.task_status, "accepted",
    )

    task.task_status = "accepted"
    task.primary_response_id = response_id
    task.updated_at = datetime.now(tz=UTC)

    resolution = InquiryResolution(
        inquiry_task_id=task_id,
        inquiry_response_id=response_id,
        resolution_status="accepted",
        effective_weight=weight,
        used_for_decision=True,
    )
    db.add(resolution)

    # Move case to monitoring if still open
    case_result = await db.execute(
        select(InquiryCase).where(
            InquiryCase.inquiry_case_id
            == task.inquiry_case_id,
        )
    )
    case = case_result.scalar_one()
    if case.case_status == "open":
        case.case_status = "monitoring"
        case.updated_at = datetime.now(
            tz=UTC,
        )

    await db.flush()
    await emit_event(
        db,
        event_type="accepted",
        aggregate_type="inquiry_response",
        aggregate_id=str(response_id),
        payload={
            "task_id": str(task_id),
            "weight": str(weight),
        },
    )
    await db.commit()
    await db.refresh(resolution)
    return resolution


async def reject_inquiry_response(
    db: AsyncSession,
    *,
    task_id: UUID,
    response_id: UUID,
    reason: str | None = None,
) -> InquiryResolution:
    """Reject a response and create a resolution.

    Transitions the task to ``rejected``.
    """
    task_result = await db.execute(
        select(InquiryTask).where(
            InquiryTask.inquiry_task_id == task_id,
        )
    )
    task = task_result.scalar_one()
    _assert_task_transition(
        task.task_status, "rejected",
    )

    task.task_status = "rejected"
    task.updated_at = datetime.now(tz=UTC)

    resolution = InquiryResolution(
        inquiry_task_id=task_id,
        inquiry_response_id=response_id,
        resolution_status="rejected",
        used_for_decision=False,
        notes=reason,
    )
    db.add(resolution)

    await db.flush()
    await emit_event(
        db,
        event_type="rejected",
        aggregate_type="inquiry_response",
        aggregate_id=str(response_id),
        payload={
            "task_id": str(task_id),
            "reason": reason or "",
        },
    )
    await db.commit()
    await db.refresh(resolution)
    return resolution


async def supersede_task(
    db: AsyncSession,
    *,
    task_id: UUID,
) -> InquiryTask:
    """Mark a task as superseded."""
    result = await db.execute(
        select(InquiryTask).where(
            InquiryTask.inquiry_task_id == task_id,
        )
    )
    task = result.scalar_one()
    _assert_task_transition(
        task.task_status, "superseded",
    )
    task.task_status = "superseded"
    task.updated_at = datetime.now(tz=UTC)

    await emit_event(
        db,
        event_type="superseded",
        aggregate_type="inquiry_task",
        aggregate_id=str(task_id),
        payload={
            "case_id": str(task.inquiry_case_id),
        },
    )
    await db.commit()
    await db.refresh(task)
    return task


async def expire_task(
    db: AsyncSession,
    *,
    task_id: UUID,
) -> InquiryTask:
    """Expire a single task."""
    result = await db.execute(
        select(InquiryTask).where(
            InquiryTask.inquiry_task_id == task_id,
        )
    )
    task = result.scalar_one()
    _assert_task_transition(
        task.task_status, "expired",
    )
    task.task_status = "expired"
    task.updated_at = datetime.now(tz=UTC)

    await emit_event(
        db,
        event_type="expired",
        aggregate_type="inquiry_task",
        aggregate_id=str(task_id),
        payload={
            "case_id": str(task.inquiry_case_id),
        },
    )
    await db.commit()
    await db.refresh(task)
    return task


async def expire_overdue_tasks(
    db: AsyncSession,
) -> int:
    """Batch-expire all overdue tasks.

    Returns the count of expired tasks.
    """
    now = datetime.now(tz=UTC)
    expirable = [
        "draft",
        "visible",
        "claimed",
        "awaiting_response",
    ]
    result = await db.execute(
        select(InquiryTask).where(
            InquiryTask.task_status.in_(expirable),
            InquiryTask.deadline_at < now,
        )
    )
    tasks = result.scalars().all()
    count = 0
    for t in tasks:
        t.task_status = "expired"
        t.updated_at = now
        await emit_event(
            db,
            event_type="expired",
            aggregate_type="inquiry_task",
            aggregate_id=str(t.inquiry_task_id),
            payload={
                "case_id": str(
                    t.inquiry_case_id,
                ),
                "batch": True,
            },
        )
        count += 1
    if count > 0:
        await db.commit()
    return count


# ---------------------------------------------------------------
# Presence
# ---------------------------------------------------------------
async def update_presence(
    db: AsyncSession,
    *,
    user_id: UUID,
    availability_state: str,
    focus_mode: str,
    can_receive_push: bool = True,
    can_receive_urgent: bool = True,
) -> InquiryPresence:
    """Upsert operator presence."""
    result = await db.execute(
        select(InquiryPresence).where(
            InquiryPresence.user_id == user_id,
        )
    )
    presence = result.scalar_one_or_none()
    if presence is None:
        presence = InquiryPresence(
            user_id=user_id,
            availability_state=availability_state,
            focus_mode=focus_mode,
            can_receive_push=can_receive_push,
            can_receive_urgent=can_receive_urgent,
        )
        db.add(presence)
    else:
        presence.availability_state = (
            availability_state
        )
        presence.focus_mode = focus_mode
        presence.can_receive_push = can_receive_push
        presence.can_receive_urgent = (
            can_receive_urgent
        )
    await db.commit()
    await db.refresh(presence)
    return presence


# ---------------------------------------------------------------
# Tray query
# ---------------------------------------------------------------
async def get_tray(
    db: AsyncSession,
) -> list[dict[str, Any]]:
    """Build the inquiry tray items.

    Returns lightweight dicts suitable for
    InquiryTrayItem serialisation.  Equivalent to
    querying ``vw_inquiry_tray``.
    """
    now = datetime.now(tz=UTC)
    active_statuses = [
        "visible",
        "claimed",
        "awaiting_response",
        "submitted",
        "parsed",
    ]
    stmt = (
        select(
            InquiryTask.inquiry_task_id,
            InquiryTask.inquiry_case_id,
            InquiryCase.inquiry_kind,
            InquiryCase.market_profile_code,
            InquiryCase.primary_symbol,
            InquiryTask.task_status,
            InquiryTask.priority_score,
            InquiryTask.sla_class,
            InquiryTask.deadline_at,
            InquiryTask.question_title,
        )
        .join(
            InquiryCase,
            InquiryTask.inquiry_case_id
            == InquiryCase.inquiry_case_id,
        )
        .where(
            InquiryTask.task_status.in_(
                active_statuses,
            ),
        )
        .order_by(
            InquiryTask.priority_score.desc(),
            InquiryTask.deadline_at.asc(),
        )
    )
    rows = (await db.execute(stmt)).all()

    items: list[dict[str, Any]] = []
    for row in rows:
        deadline = row.deadline_at
        if deadline is None:
            bucket = "normal"
        elif deadline < now:
            bucket = "overdue"
        elif (
            deadline.timestamp() - now.timestamp()
        ) < 1800:
            bucket = "due_soon"
        else:
            bucket = "normal"

        items.append(
            {
                "task_id": row.inquiry_task_id,
                "case_id": row.inquiry_case_id,
                "inquiry_kind": row.inquiry_kind,
                "market_profile_code": (
                    row.market_profile_code
                ),
                "primary_symbol": (
                    row.primary_symbol
                ),
                "task_status": row.task_status,
                "priority_score": (
                    row.priority_score
                ),
                "sla_class": row.sla_class,
                "deadline_at": row.deadline_at,
                "question_title": (
                    row.question_title
                ),
                "time_bucket": bucket,
            }
        )
    return items


# ---------------------------------------------------------------
# Metrics query
# ---------------------------------------------------------------
async def get_metrics(
    db: AsyncSession,
) -> dict[str, Any]:
    """Compute live inquiry metrics."""
    now = datetime.now(tz=UTC)

    open_q = await db.execute(
        select(func.count()).select_from(
            InquiryTask,
        ).where(
            InquiryTask.task_status.in_(
                [
                    "visible",
                    "claimed",
                    "awaiting_response",
                    "submitted",
                    "parsed",
                ],
            ),
        )
    )
    open_count = open_q.scalar_one()

    overdue_q = await db.execute(
        select(func.count()).select_from(
            InquiryTask,
        ).where(
            InquiryTask.task_status.in_(
                [
                    "visible",
                    "claimed",
                    "awaiting_response",
                ],
            ),
            InquiryTask.deadline_at < now,
        )
    )
    overdue_count = overdue_q.scalar_one()

    # due_soon: deadline within 30 minutes
    from datetime import timedelta
    soon = now + timedelta(minutes=30)
    due_soon_q = await db.execute(
        select(func.count()).select_from(
            InquiryTask,
        ).where(
            InquiryTask.task_status.in_(
                [
                    "visible",
                    "claimed",
                    "awaiting_response",
                ],
            ),
            InquiryTask.deadline_at >= now,
            InquiryTask.deadline_at <= soon,
        )
    )
    due_soon_count = due_soon_q.scalar_one()

    return {
        "open_count": open_count,
        "due_soon_count": due_soon_count,
        "overdue_count": overdue_count,
        "supersede_rate": None,
        "response_latency_p50_sec": None,
        "response_latency_p95_sec": None,
        "accept_rate": None,
        "late_response_rate": None,
        "manual_uplift_score_delta": None,
    }
