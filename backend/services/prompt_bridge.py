"""Manual expert bridge service.

Manages prompt task lifecycle and determines when
manual review is needed.

Lifecycle:
    created -> visible -> submitted -> parsed
        -> accepted / rejected / expired / canceled
    needs_reformat can loop back to submitted.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.outbox import emit_event
from backend.models.forecasting import (
    DecisionLedger,
    PromptResponse,
    PromptTask,
)

# ------------------------------------------------------------------
# Escalation triggers
# ------------------------------------------------------------------

def should_escalate_to_manual(
    *,
    materiality: float | None,
    confidence: float | None,
    event_type: str,
    is_novel_event_type: bool = False,
    position_size_pct: float = 0.0,
) -> tuple[bool, str]:
    """Decide if a decision needs manual review.

    Returns (should_escalate, reason).

    Triggers per spec doc 12:
    - materiality high + confidence low
    - novel / unknown event types
    - macro vs single-name conflict (covered by caller)
    - large position size
    """
    if is_novel_event_type:
        return True, "novel_event_type"

    if (
        materiality is not None
        and confidence is not None
        and materiality > 0.7
        and confidence < 0.5
    ):
        return True, "high_materiality_low_confidence"

    if position_size_pct > 0.05:
        return True, "large_position"

    return False, ""


# ------------------------------------------------------------------
# Task lifecycle helpers
# ------------------------------------------------------------------

_VALID_TRANSITIONS: dict[str, list[str]] = {
    "created": ["visible", "canceled"],
    "visible": ["submitted", "expired", "canceled"],
    "submitted": ["parsed", "needs_reformat"],
    "parsed": ["accepted", "rejected"],
    "needs_reformat": [
        "submitted",
        "expired",
        "canceled",
    ],
}


async def create_prompt_task(
    db: AsyncSession,
    *,
    decision_id: UUID,
    task_type: str,
    prompt_text: str,
    deadline_at: datetime,
    evidence_bundle_json: list[Any] | None = None,
    prompt_template_id: str = "default_review_v1",
    prompt_version: str = "1.0.0",
    created_by: UUID | None = None,
    # Allow pass-through of schema fields from
    # PromptTaskCreate.model_dump().
    prompt_schema_name: str = "prompt_task",
    prompt_schema_version: str = "1.0.0",
) -> PromptTask:
    """Create a new prompt task for manual review."""
    task = PromptTask(
        decision_id=decision_id,
        task_type=task_type,
        prompt_template_id=prompt_template_id,
        prompt_version=prompt_version,
        prompt_text=prompt_text,
        prompt_schema_name=prompt_schema_name,
        prompt_schema_version=prompt_schema_version,
        evidence_bundle_json=evidence_bundle_json or [],
        deadline_at=deadline_at,
        status="created",
        created_by=created_by,
    )
    db.add(task)
    await db.flush()

    # Link the decision to this prompt task.
    await db.execute(
        update(DecisionLedger)
        .where(
            DecisionLedger.decision_id == decision_id,
        )
        .values(
            decision_status="waiting_manual",
            waiting_on_prompt_task_id=(
                task.prompt_task_id
            ),
        )
    )

    # Emit outbox event within the same transaction
    await emit_event(
        db,
        event_type="created",
        aggregate_type="prompt_task",
        aggregate_id=str(task.prompt_task_id),
        payload={
            "decision_id": str(decision_id),
            "task_type": task_type,
        },
    )

    await db.commit()
    await db.refresh(task)
    return task


async def transition_task_status(
    db: AsyncSession,
    *,
    prompt_task_id: UUID,
    new_status: str,
) -> PromptTask:
    """Transition a prompt task to a new status.

    Raises ValueError when the transition is invalid.
    """
    result = await db.execute(
        select(PromptTask).where(
            PromptTask.prompt_task_id == prompt_task_id,
        )
    )
    task = result.scalar_one()

    allowed = _VALID_TRANSITIONS.get(task.status, [])
    if new_status not in allowed:
        msg = (
            f"Cannot transition from "
            f"'{task.status}' to '{new_status}'"
        )
        raise ValueError(msg)

    task.status = new_status
    await db.commit()
    await db.refresh(task)
    return task


async def submit_response(
    db: AsyncSession,
    *,
    prompt_task_id: UUID,
    model_name: str,
    raw_response: str,
    parsed_json: dict[str, Any] | None = None,
    submitted_by: UUID | None = None,
) -> PromptResponse:
    """Submit a response to a prompt task.

    The task must be in ``visible`` or
    ``needs_reformat`` status.
    """
    task_result = await db.execute(
        select(PromptTask).where(
            PromptTask.prompt_task_id == prompt_task_id,
        )
    )
    task = task_result.scalar_one()

    submittable = ("visible", "needs_reformat")
    if task.status not in submittable:
        msg = (
            "Cannot submit response: "
            f"task status is '{task.status}'"
        )
        raise ValueError(msg)

    schema_valid = parsed_json is not None

    response = PromptResponse(
        prompt_task_id=prompt_task_id,
        submitted_by=submitted_by,
        model_name_user_entered=model_name,
        raw_response=raw_response,
        parsed_json=parsed_json,
        schema_valid=schema_valid,
    )
    db.add(response)

    # Transition task to submitted.
    task.status = "submitted"

    await db.commit()
    await db.refresh(response)
    return response


async def accept_response(
    db: AsyncSession,
    *,
    prompt_task_id: UUID,
    prompt_response_id: UUID,
    final_weight: float = 1.0,
) -> None:
    """Accept a response and update the decision.

    Marks the response as accepted for scoring,
    transitions the task to ``accepted``, and sets
    the linked decision back to ``approved``.
    """
    # Mark response as accepted.
    await db.execute(
        update(PromptResponse)
        .where(
            PromptResponse.prompt_response_id
            == prompt_response_id,
        )
        .values(
            accepted_for_scoring=True,
            final_weight=final_weight,
        )
    )

    # Transition the task.
    task_result = await db.execute(
        select(PromptTask).where(
            PromptTask.prompt_task_id == prompt_task_id,
        )
    )
    task = task_result.scalar_one()
    task.status = "accepted"

    # Unblock the linked decision.
    await db.execute(
        update(DecisionLedger)
        .where(
            DecisionLedger.decision_id == task.decision_id,
        )
        .values(decision_status="approved")
    )

    await db.commit()
