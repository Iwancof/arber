"""Postmortem API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.models.feedback import OutcomeLedger, PostmortemLedger
from backend.schemas.feedback import (
    OutcomeRead,
    PostmortemList,
    PostmortemRead,
)

router = APIRouter(tags=["postmortems"])


@router.get("/postmortems", response_model=PostmortemList)
async def list_postmortems(
    verdict: str | None = Query(default=None),
    requires_source_review: bool | None = Query(default=None),
    requires_prompt_review: bool | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> PostmortemList:
    stmt = select(PostmortemLedger)
    count_stmt = select(func.count()).select_from(PostmortemLedger)
    if verdict:
        stmt = stmt.where(PostmortemLedger.verdict == verdict)
        count_stmt = count_stmt.where(
            PostmortemLedger.verdict == verdict
        )
    if requires_source_review is not None:
        stmt = stmt.where(
            PostmortemLedger.requires_source_review
            == requires_source_review
        )
        count_stmt = count_stmt.where(
            PostmortemLedger.requires_source_review
            == requires_source_review
        )
    if requires_prompt_review is not None:
        stmt = stmt.where(
            PostmortemLedger.requires_prompt_review
            == requires_prompt_review
        )
        count_stmt = count_stmt.where(
            PostmortemLedger.requires_prompt_review
            == requires_prompt_review
        )

    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(
        stmt.offset(offset)
        .limit(limit)
        .order_by(PostmortemLedger.created_at.desc())
    )
    items = [
        PostmortemRead.model_validate(r)
        for r in result.scalars().all()
    ]
    return PostmortemList(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get(
    "/postmortems/{postmortem_id}",
    response_model=PostmortemRead,
)
async def get_postmortem(
    postmortem_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PostmortemRead:
    result = await db.execute(
        select(PostmortemLedger).where(
            PostmortemLedger.postmortem_id == postmortem_id
        )
    )
    pm = result.scalar_one_or_none()
    if pm is None:
        raise HTTPException(
            status_code=404, detail="Postmortem not found"
        )
    return PostmortemRead.model_validate(pm)


@router.get(
    "/outcomes/{forecast_id}",
    response_model=list[OutcomeRead],
)
async def list_outcomes(
    forecast_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[OutcomeRead]:
    result = await db.execute(
        select(OutcomeLedger)
        .where(OutcomeLedger.forecast_id == forecast_id)
        .order_by(OutcomeLedger.horizon_code)
    )
    return [
        OutcomeRead.model_validate(r)
        for r in result.scalars().all()
    ]
