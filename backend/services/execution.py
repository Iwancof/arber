"""Order execution service.

Bridges decisions to broker adapters, manages order lifecycle,
and tracks positions. Respects kill switches and execution modes.
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.broker.base import (
    BrokerAdapter,
    OrderIntent,
)
from backend.models.core import Instrument
from backend.models.execution import (
    ExecutionFill,
    OrderLedger,
    PositionSnapshot,
)
from backend.models.forecasting import DecisionLedger
from backend.models.ops import KillSwitch


async def check_kill_switch(
    db: AsyncSession,
    *,
    scope_type: str = "global",
    scope_key: str = "all",
) -> KillSwitch | None:
    """Check if a kill switch is active for scope."""
    result = await db.execute(
        select(KillSwitch).where(
            KillSwitch.scope_type == scope_type,
            KillSwitch.scope_key == scope_key,
            KillSwitch.active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def submit_order(
    db: AsyncSession,
    broker: BrokerAdapter,
    *,
    decision_id: UUID,
    execution_mode: str = "paper",
) -> OrderLedger:
    """Submit an order based on a decision.

    Checks kill switch, loads decision and instrument,
    submits to broker, records in order ledger.
    """
    # Check global kill switch
    global_ks = await check_kill_switch(db)
    if global_ks:
        raise RuntimeError(
            f"Kill switch active: {global_ks.reason}"
        )

    # Load decision
    d_result = await db.execute(
        select(DecisionLedger).where(
            DecisionLedger.decision_id == decision_id
        )
    )
    decision = d_result.scalar_one()

    # Load forecast to get instrument
    from backend.models.forecasting import ForecastLedger

    f_result = await db.execute(
        select(ForecastLedger).where(
            ForecastLedger.forecast_id
            == decision.forecast_id
        )
    )
    forecast = f_result.scalar_one()

    # Load instrument
    i_result = await db.execute(
        select(Instrument).where(
            Instrument.instrument_id
            == forecast.instrument_id
        )
    )
    instrument = i_result.scalar_one()

    # Determine side from action
    side = (
        "buy"
        if decision.action == "long_candidate"
        else "sell"
    )

    # Build order intent
    qty = decision.size_cap or Decimal("1")
    intent = OrderIntent(
        instrument_id=instrument.instrument_id,
        symbol=instrument.symbol,
        side=side,
        quantity=qty,
        order_type="market",
        decision_id=decision_id,
        execution_mode=execution_mode,
    )

    # Submit to broker
    status = await broker.submit(intent)

    # Record in order ledger
    order = OrderLedger(
        decision_id=decision_id,
        instrument_id=instrument.instrument_id,
        execution_mode=execution_mode,
        broker_name=broker.adapter_code,
        client_order_id=status.client_order_id,
        broker_order_id=status.broker_order_id,
        side=side,
        order_type="market",
        time_in_force="day",
        session_type="regular",
        qty=qty,
        status=status.status,
        status_reason=status.status_reason,
    )
    db.add(order)
    await db.flush()

    # Record fills if any
    if hasattr(broker, "get_fills"):
        fills = broker.get_fills(
            status.client_order_id
        )
        for f in fills:
            fill = ExecutionFill(
                order_id=order.order_id,
                fill_time=f.fill_time,
                fill_price=f.fill_price,
                fill_qty=f.fill_qty,
                fee_estimate=f.fee_estimate,
                liquidity_flag=f.liquidity_flag,
                fill_source=execution_mode,
            )
            db.add(fill)

    # Update decision status
    decision.decision_status = "submitted_to_execution"

    await db.commit()
    await db.refresh(order)
    return order


async def take_position_snapshot(
    db: AsyncSession,
    broker: BrokerAdapter,
    *,
    execution_mode: str = "paper",
) -> list[PositionSnapshot]:
    """Take a snapshot of all current positions."""
    positions = await broker.get_positions()
    snapshots: list[PositionSnapshot] = []

    for pos in positions:
        snap = PositionSnapshot(
            as_of=datetime.now(UTC),
            execution_mode=execution_mode,
            instrument_id=pos.instrument_id,
            position_qty=pos.position_qty,
            average_cost=pos.average_cost,
            mark_price=pos.mark_price,
            unrealized_pnl=pos.unrealized_pnl,
            snapshot_json={},
        )
        db.add(snap)
        snapshots.append(snap)

    await db.commit()
    for s in snapshots:
        await db.refresh(s)
    return snapshots
