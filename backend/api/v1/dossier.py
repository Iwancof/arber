"""Decision dossier API endpoint.

The dossier is the central end-to-end view of one decision:
event -> forecast -> reasoning -> decision -> orders -> outcomes.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.models.content import EventLedger
from backend.models.execution import OrderLedger
from backend.models.feedback import OutcomeLedger
from backend.models.forecasting import (
    DecisionLedger,
    DecisionReason,
    ForecastHorizon,
    ForecastLedger,
    PromptTask,
    ReasoningTrace,
)
from backend.schemas.forecasting import (
    DecisionLedgerRead,
    DecisionReasonRead,
    DossierRead,
    ForecastHorizonRead,
    ForecastLedgerRead,
    ReasoningTraceRead,
)

router = APIRouter(tags=["dossier"])


@router.get("/decisions/{decision_id}", response_model=DossierRead)
async def get_decision_dossier(
    decision_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> DossierRead:
    """Get the full decision dossier aggregate.

    Returns the decision with its linked forecast, event,
    reasoning trace, prompt tasks, orders, and outcomes.
    """
    # Decision
    d_result = await db.execute(
        select(DecisionLedger).where(
            DecisionLedger.decision_id == decision_id
        )
    )
    decision = d_result.scalar_one_or_none()
    if decision is None:
        raise HTTPException(status_code=404, detail="Decision not found")

    # Decision reasons
    reasons_result = await db.execute(
        select(DecisionReason).where(
            DecisionReason.decision_id == decision_id
        )
    )
    reasons = [
        DecisionReasonRead.model_validate(r)
        for r in reasons_result.scalars().all()
    ]
    decision_read = DecisionLedgerRead(
        decision_id=decision.decision_id,
        forecast_id=decision.forecast_id,
        market_profile_id=decision.market_profile_id,
        execution_mode=decision.execution_mode,
        score=decision.score,
        action=decision.action,
        decision_status=decision.decision_status,
        policy_version=decision.policy_version,
        size_cap=decision.size_cap,
        reason_codes_json=decision.reason_codes_json,
        decided_at=decision.decided_at,
        reasons=reasons,
    )

    # Forecast
    forecast_read = None
    forecast = None
    if decision.forecast_id:
        f_result = await db.execute(
            select(ForecastLedger).where(
                ForecastLedger.forecast_id == decision.forecast_id
            )
        )
        forecast = f_result.scalar_one_or_none()
        if forecast:
            h_result = await db.execute(
                select(ForecastHorizon).where(
                    ForecastHorizon.forecast_id == forecast.forecast_id
                )
            )
            horizons = [
                ForecastHorizonRead.model_validate(h)
                for h in h_result.scalars().all()
            ]
            forecast_read = ForecastLedgerRead(
                forecast_id=forecast.forecast_id,
                event_id=forecast.event_id,
                instrument_id=forecast.instrument_id,
                benchmark_instrument_id=forecast.benchmark_instrument_id,
                market_profile_id=forecast.market_profile_id,
                reasoning_trace_id=forecast.reasoning_trace_id,
                model_family=forecast.model_family,
                model_version=forecast.model_version,
                worker_id=forecast.worker_id,
                prompt_template_id=forecast.prompt_template_id,
                prompt_version=forecast.prompt_version,
                forecast_mode=forecast.forecast_mode,
                forecasted_at=forecast.forecasted_at,
                confidence=forecast.confidence,
                no_trade_reason_codes_json=forecast.no_trade_reason_codes_json,
                forecast_json=forecast.forecast_json,
                horizons=horizons,
            )

    # Event
    event_dict = None
    if forecast and forecast.event_id:
        e_result = await db.execute(
            select(EventLedger).where(
                EventLedger.event_id == forecast.event_id
            )
        )
        event = e_result.scalar_one_or_none()
        if event:
            event_dict = {
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "direction_hint": event.direction_hint,
                "materiality": str(event.materiality) if event.materiality else None,
                "event_time": event.event_time.isoformat() if event.event_time else None,
                "event_json": event.event_json,
            }

    # Reasoning trace
    trace_read = None
    if forecast and forecast.reasoning_trace_id:
        t_result = await db.execute(
            select(ReasoningTrace).where(
                ReasoningTrace.reasoning_trace_id == forecast.reasoning_trace_id
            )
        )
        trace = t_result.scalar_one_or_none()
        if trace:
            trace_read = ReasoningTraceRead.model_validate(trace)

    # Prompt tasks
    pt_result = await db.execute(
        select(PromptTask).where(PromptTask.decision_id == decision_id)
    )
    prompt_tasks = [
        {
            "prompt_task_id": str(pt.prompt_task_id),
            "task_type": pt.task_type,
            "status": pt.status,
            "deadline_at": pt.deadline_at.isoformat() if pt.deadline_at else None,
        }
        for pt in pt_result.scalars().all()
    ]

    # Orders
    orders_result = await db.execute(
        select(OrderLedger).where(OrderLedger.decision_id == decision_id)
    )
    orders = [
        {
            "order_id": str(o.order_id),
            "side": o.side,
            "qty": str(o.qty),
            "status": o.status,
            "submitted_at": o.submitted_at.isoformat(),
        }
        for o in orders_result.scalars().all()
    ]

    # Outcomes
    outcomes = []
    if forecast:
        oc_result = await db.execute(
            select(OutcomeLedger).where(
                OutcomeLedger.forecast_id == forecast.forecast_id
            )
        )
        outcomes = [
            {
                "outcome_id": str(oc.outcome_id),
                "horizon_code": oc.horizon_code,
                "realized_rel_return": str(oc.realized_rel_return)
                if oc.realized_rel_return
                else None,
            }
            for oc in oc_result.scalars().all()
        ]

    return DossierRead(
        decision=decision_read,
        forecast=forecast_read,
        event=event_dict,
        reasoning_trace=trace_read,
        prompt_tasks=prompt_tasks,
        orders=orders,
        outcomes=outcomes,
    )
