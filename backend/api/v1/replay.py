"""Replay job API endpoints."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.models.ops import JobRun
from backend.schemas.common import OrmBase, PaginatedResponse

router = APIRouter(tags=["replay"])


class JobRunRead(OrmBase):
    """Job run response schema."""
    job_run_id: UUID
    job_type: str
    execution_mode: str
    status: str
    requested_by: UUID | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    job_args_json: dict
    result_json: dict


class JobRunList(PaginatedResponse):
    """Paginated list of job runs."""
    items: list[JobRunRead]


class ReplayJobCreate(BaseModel):
    """Replay job creation request."""
    market_profile_id: UUID
    from_time: datetime
    to_time: datetime
    requested_by: UUID | None = None


@router.post("/replay-jobs", response_model=JobRunRead, status_code=202)
async def create_replay(
    body: ReplayJobCreate,
    db: AsyncSession = Depends(get_db),
) -> JobRunRead:
    """Create and queue a replay job."""
    from backend.services.replay import create_replay_job
    job = await create_replay_job(
        db,
        market_profile_id=body.market_profile_id,
        from_time=body.from_time,
        to_time=body.to_time,
        requested_by=body.requested_by,
    )
    return JobRunRead.model_validate(job)


@router.post(
    "/replay-jobs/{job_id}/run",
    response_model=JobRunRead,
)
async def execute_replay(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> JobRunRead:
    """Execute a queued replay job synchronously."""
    from backend.services.replay import run_replay
    result = await db.execute(
        select(JobRun).where(JobRun.job_run_id == job_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "queued":
        raise HTTPException(
            status_code=409,
            detail=f"Job status is '{job.status}', expected 'queued'",
        )

    completed = await run_replay(db, job_run_id=job_id)
    return JobRunRead.model_validate(completed)


@router.get("/replay-jobs", response_model=JobRunList)
async def list_replay_jobs(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> JobRunList:
    stmt = select(JobRun).where(JobRun.job_type == "replay")
    count_stmt = select(func.count()).select_from(JobRun).where(
        JobRun.job_type == "replay"
    )
    if status:
        stmt = stmt.where(JobRun.status == status)
        count_stmt = count_stmt.where(JobRun.status == status)

    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(stmt.offset(offset).limit(limit))
    items = [JobRunRead.model_validate(r) for r in result.scalars().all()]
    return JobRunList(items=items, total=total, limit=limit, offset=offset)


@router.get("/replay-jobs/{job_id}", response_model=JobRunRead)
async def get_replay_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> JobRunRead:
    result = await db.execute(
        select(JobRun).where(JobRun.job_run_id == job_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobRunRead.model_validate(job)
