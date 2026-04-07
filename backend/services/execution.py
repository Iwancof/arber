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
from backend.adapters.broker.registry import validate_adapter_for_mode
from backend.core.execution_mode import (
    ExecutionMode,
    validate_mode_for_order_submission,
)
from backend.core.kill_switch import check_trade_allowed
from backend.core.outbox import emit_event
from backend.models.core import Instrument
from backend.models.execution import (
    ExecutionFill,
    OrderLedger,
    PositionSnapshot,
)
from backend.models.forecasting import DecisionLedger


async def submit_order(
    db: AsyncSession,
    broker: BrokerAdapter,
    *,
    decision_id: UUID,
    execution_mode: str = "paper",
) -> OrderLedger:
    """Submit an order based on a decision.

    Checks execution mode safety guards, kill switch,
    loads decision and instrument, submits to broker,
    records in order ledger.
    """
    # Layer 1: Service-level mode guard
    mode = ExecutionMode(execution_mode)
    validate_mode_for_order_submission(mode)

    # Layer 2: Adapter-level mode guard
    validate_adapter_for_mode(broker, mode)

    # Load decision
    d_result = await db.execute(
        select(DecisionLedger).where(
            DecisionLedger.decision_id == decision_id
        )
    )
    decision = d_result.scalar_one()

    # Determine side from action (needed for kill switch check)
    side = (
        "buy"
        if decision.action == "long_candidate"
        else "sell"
    )

    # Scoped kill switch check (after loading decision for side)
    await check_trade_allowed(db, side=side)

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

    # Emit outbox event within the same transaction
    await emit_event(
        db,
        event_type="submitted",
        aggregate_type="order",
        aggregate_id=str(order.order_id),
        payload={
            "decision_id": str(decision_id),
            "side": side,
            "qty": str(qty),
        },
    )

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
