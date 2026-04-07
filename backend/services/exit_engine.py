"""Exit engine for paper trading.

Implements 4 exit strategies:
1. Time-based close (1d or 5d horizon)
2. Hard stop (-2% for 1d, -3% for 5d)
3. Opposite signal close
4. Manual close (via API)
"""

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.broker.base import BrokerAdapter
from backend.core.outbox import emit_event
from backend.models.execution import OrderLedger

logger = logging.getLogger("eos.exit_engine")

# Hard stop percentages
STOP_1D = Decimal("-0.02")  # -2%
STOP_5D = Decimal("-0.03")  # -3%


async def check_time_exits(
    db: AsyncSession,
    broker: BrokerAdapter,
) -> int:
    """Close positions that have exceeded their
    trade horizon.

    Returns number of positions closed.
    """
    closed = 0
    now = datetime.now(UTC)

    # Find open orders with time-based exit
    result = await db.execute(
        select(OrderLedger).where(
            OrderLedger.status == "filled",
            OrderLedger.execution_mode == "paper",
        )
    )
    orders = list(result.scalars().all())

    for order in orders:
        meta = order.metadata_json or {}
        horizon = meta.get(
            "trade_horizon", "5d"
        )
        entry_time = order.submitted_at

        if horizon == "1d":
            exit_after = (
                entry_time + timedelta(days=1)
            )
        else:
            exit_after = (
                entry_time + timedelta(days=5)
            )

        if now >= exit_after:
            logger.info(
                "Time exit: %s %s (horizon=%s)",
                order.client_order_id,
                meta.get("symbol", "?"),
                horizon,
            )
            await _close_position(
                db, broker, order, "time_exit"
            )
            closed += 1

    return closed


async def check_stop_exits(
    db: AsyncSession,
    broker: BrokerAdapter,
) -> int:
    """Close positions that hit hard stop.

    Returns number of positions closed.
    """
    closed = 0
    positions = await broker.get_positions()

    result = await db.execute(
        select(OrderLedger).where(
            OrderLedger.status == "filled",
            OrderLedger.execution_mode == "paper",
        )
    )
    orders = {
        o.metadata_json.get("symbol", ""): o
        for o in result.scalars().all()
        if o.metadata_json
    }

    for pos in positions:
        if pos.position_qty == 0:
            continue

        order = orders.get(pos.symbol)
        if not order:
            continue

        meta = order.metadata_json or {}
        horizon = meta.get(
            "trade_horizon", "5d"
        )
        stop_pct = (
            STOP_1D if horizon == "1d" else STOP_5D
        )

        # Calculate PnL percentage
        if (
            pos.average_cost
            and pos.average_cost > 0
        ):
            pnl_pct = (
                (pos.mark_price or Decimal("0"))
                - pos.average_cost
            ) / pos.average_cost
        else:
            continue

        if pnl_pct <= stop_pct:
            logger.info(
                "Hard stop: %s pnl=%.2f%% "
                "stop=%.2f%%",
                pos.symbol,
                float(pnl_pct * 100),
                float(stop_pct * 100),
            )
            await _close_position(
                db, broker, order, "hard_stop"
            )
            closed += 1

    return closed


async def _close_position(
    db: AsyncSession,
    broker: BrokerAdapter,
    order: OrderLedger,
    reason: str,
) -> None:
    """Close a position by submitting a reverse
    order."""
    from backend.adapters.broker.base import (
        OrderIntent,
    )

    meta = order.metadata_json or {}
    reverse_side = (
        "sell" if order.side == "buy" else "buy"
    )

    intent = OrderIntent(
        instrument_id=order.instrument_id,
        symbol=meta.get("symbol", ""),
        side=reverse_side,
        quantity=order.qty,
        order_type="market",
        execution_mode="paper",
    )

    status = await broker.submit(intent)

    # Update original order metadata
    meta["exit_reason"] = reason
    meta["exit_time"] = (
        datetime.now(UTC).isoformat()
    )
    meta["exit_order_id"] = (
        status.client_order_id
    )
    order.metadata_json = meta

    await emit_event(
        db,
        event_type="closed",
        aggregate_type="order",
        aggregate_id=str(order.order_id),
        payload={
            "reason": reason,
            "exit_order_id": (
                status.client_order_id
            ),
        },
    )
    await db.commit()
