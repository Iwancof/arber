"""Replay engine service.

Re-executes the full pipeline over historical event data:
event → forecast → decision, all in deterministic replay mode.

Critical invariant: the same decision logic path works across
all execution modes (replay/shadow/paper/micro_live/live).
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.worker.mock_worker import MockWorkerAdapter
from backend.models.content import EventLedger
from backend.models.ops import JobRun
from backend.services.decision import evaluate_forecast
from backend.services.forecast import run_forecast_pipeline


async def create_replay_job(
    db: AsyncSession,
    *,
    market_profile_id: UUID,
    from_time: datetime,
    to_time: datetime,
    requested_by: UUID | None = None,
    job_args: dict[str, Any] | None = None,
) -> JobRun:
    """Create a replay job record."""
    job = JobRun(
        job_type="replay",
        execution_mode="replay",
        status="queued",
        requested_by=requested_by,
        job_args_json={
            "market_profile_id": str(market_profile_id),
            "from_time": from_time.isoformat(),
            "to_time": to_time.isoformat(),
            **(job_args or {}),
        },
        result_json={},
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def run_replay(
    db: AsyncSession,
    *,
    job_run_id: UUID,
) -> JobRun:
    """Execute a replay job.

    Processes all events in the time range through the forecast
    and decision pipeline using the deterministic mock worker.
    """
    # Load job
    job_result = await db.execute(
        select(JobRun).where(JobRun.job_run_id == job_run_id)
    )
    job = job_result.scalar_one()

    # Start job
    job.status = "running"
    job.started_at = datetime.now(UTC)
    await db.commit()

    worker = MockWorkerAdapter()

    try:
        args = job.job_args_json
        market_profile_id = UUID(args["market_profile_id"])
        from_time = datetime.fromisoformat(args["from_time"])
        to_time = datetime.fromisoformat(args["to_time"])

        # Fetch events in range
        event_result = await db.execute(
            select(EventLedger)
            .where(
                EventLedger.market_profile_id == market_profile_id,
                EventLedger.created_at >= from_time,
                EventLedger.created_at <= to_time,
            )
            .order_by(EventLedger.created_at)
        )
        events = list(event_result.scalars().all())

        processed = 0
        errors = 0
        forecast_ids: list[str] = []
        decision_ids: list[str] = []

        for event in events:
            try:
                # Skip events without instrument
                if not event.issuer_instrument_id:
                    continue

                # Run forecast pipeline
                forecast = await run_forecast_pipeline(
                    db,
                    worker,
                    event_id=event.event_id,
                    instrument_id=event.issuer_instrument_id,
                    market_profile_id=market_profile_id,
                    execution_mode="replay",
                )
                forecast_ids.append(str(forecast.forecast_id))

                # Run decision evaluation
                decision = await evaluate_forecast(
                    db,
                    forecast_id=forecast.forecast_id,
                    execution_mode="replay",
                )
                decision_ids.append(str(decision.decision_id))
                processed += 1

            except Exception:
                errors += 1
                continue

        # Complete job
        job.status = "succeeded"
        job.finished_at = datetime.now(UTC)
        job.result_json = {
            "events_found": len(events),
            "processed": processed,
            "errors": errors,
            "forecast_ids": forecast_ids,
            "decision_ids": decision_ids,
        }

    except Exception as exc:
        job.status = "failed"
        job.finished_at = datetime.now(UTC)
        job.result_json = {"error": str(exc)}

    await db.commit()
    await db.refresh(job)
    return job
