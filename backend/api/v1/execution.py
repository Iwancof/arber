"""Execution, orders, positions, and kill switch endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import (
    Capability,
    CurrentUser,
    require_capability,
)
from backend.db.session import get_db
from backend.models.execution import (
    ExecutionFill,
    OrderLedger,
    PositionSnapshot,
)
from backend.models.ops import KillSwitch
from backend.schemas.execution import (
    ExecutionFillRead,
    KillSwitchActivate,
    KillSwitchRead,
    OrderLedgerRead,
    OrderList,
    PositionSnapshotRead,
)

router = APIRouter(tags=["execution"])


# --- Orders ---


@router.get("/orders", response_model=OrderList)
async def list_orders(
    execution_mode: str | None = Query(default=None),
    status: str | None = Query(default=None),
    instrument_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> OrderList:
    """List orders with optional filters."""
    stmt = select(OrderLedger)
    count_stmt = select(
        func.count()
    ).select_from(OrderLedger)
    if execution_mode:
        stmt = stmt.where(
            OrderLedger.execution_mode
            == execution_mode
        )
        count_stmt = count_stmt.where(
            OrderLedger.execution_mode
            == execution_mode
        )
    if status:
        stmt = stmt.where(
            OrderLedger.status == status
        )
        count_stmt = count_stmt.where(
            OrderLedger.status == status
        )
    if instrument_id:
        stmt = stmt.where(
            OrderLedger.instrument_id == instrument_id
        )
        count_stmt = count_stmt.where(
            OrderLedger.instrument_id == instrument_id
        )

    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(
        stmt.offset(offset)
        .limit(limit)
        .order_by(OrderLedger.submitted_at.desc())
    )
    items = [
        OrderLedgerRead.model_validate(r)
        for r in result.scalars().all()
    ]
    return OrderList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/orders/{order_id}",
    response_model=OrderLedgerRead,
)
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> OrderLedgerRead:
    """Get a single order by ID."""
    result = await db.execute(
        select(OrderLedger).where(
            OrderLedger.order_id == order_id
        )
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )
    return OrderLedgerRead.model_validate(order)


@router.get(
    "/orders/{order_id}/fills",
    response_model=list[ExecutionFillRead],
)
async def list_fills(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ExecutionFillRead]:
    """List fills for a specific order."""
    result = await db.execute(
        select(ExecutionFill)
        .where(ExecutionFill.order_id == order_id)
        .order_by(ExecutionFill.fill_time)
    )
    return [
        ExecutionFillRead.model_validate(r)
        for r in result.scalars().all()
    ]


# --- Positions ---


@router.get(
    "/positions",
    response_model=list[PositionSnapshotRead],
)
async def list_positions(
    execution_mode: str = Query(default="paper"),
    db: AsyncSession = Depends(get_db),
) -> list[PositionSnapshotRead]:
    """List position snapshots by execution mode."""
    result = await db.execute(
        select(PositionSnapshot)
        .where(
            PositionSnapshot.execution_mode
            == execution_mode
        )
        .order_by(PositionSnapshot.as_of.desc())
        .limit(100)
    )
    return [
        PositionSnapshotRead.model_validate(r)
        for r in result.scalars().all()
    ]


# --- Kill Switches ---


@router.get(
    "/kill-switches",
    response_model=list[KillSwitchRead],
)
async def list_kill_switches(
    active: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[KillSwitchRead]:
    """List kill switches, optionally filtered."""
    stmt = select(KillSwitch)
    if active is not None:
        stmt = stmt.where(KillSwitch.active == active)
    result = await db.execute(
        stmt.order_by(KillSwitch.activated_at.desc())
    )
    return [
        KillSwitchRead.model_validate(r)
        for r in result.scalars().all()
    ]


@router.post(
    "/kill-switches/activate",
    response_model=KillSwitchRead,
    status_code=201,
)
async def activate_kill_switch(
    body: KillSwitchActivate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(
        require_capability(Capability.CAN_KILL_SWITCH)
    ),
) -> KillSwitchRead:
    """Activate a new kill switch."""
    ks = KillSwitch(
        scope_type=body.scope_type,
        scope_key=body.scope_key,
        active=True,
        reason=body.reason,
        activated_by=body.activated_by,
    )
    db.add(ks)
    await db.commit()
    await db.refresh(ks)
    return KillSwitchRead.model_validate(ks)


@router.post(
    "/kill-switches/{kill_switch_id}/clear",
    response_model=KillSwitchRead,
)
async def clear_kill_switch(
    kill_switch_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(
        require_capability(Capability.CAN_KILL_SWITCH)
    ),
) -> KillSwitchRead:
    """Clear (deactivate) a kill switch."""
    from datetime import UTC, datetime

    result = await db.execute(
        select(KillSwitch).where(
            KillSwitch.kill_switch_id
            == kill_switch_id
        )
    )
    ks = result.scalar_one_or_none()
    if ks is None:
        raise HTTPException(
            status_code=404,
            detail="Kill switch not found",
        )
    ks.active = False
    ks.cleared_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(ks)
    return KillSwitchRead.model_validate(ks)
