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
    orders = [
        o for o in result.scalars().all()
        if not (o.metadata_json or {}).get("exited")
    ]

    for order in orders:
        meta = order.metadata_json or {}
        horizon = meta.get(
            "trade_horizon", "5d"
        )
        # Use updated_at as proxy for filled_at
        # (set when status changes to filled)
        entry_time = (
            order.updated_at or order.submitted_at
        )

        # Approximate trading days (skip weekends)
        # 1 trading day ≈ 2 cal, 5 trading ≈ 7 cal
        cal_days = 2 if horizon == "1d" else 7
        exit_after = (
            entry_time + timedelta(days=cal_days)
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
        and not o.metadata_json.get("exited")
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

        # Calculate PnL percentage (side-aware)
        if (
            pos.average_cost
            and pos.average_cost > 0
        ):
            mark = pos.mark_price or Decimal("0")
            if order.side == "sell":  # short
                pnl_pct = (
                    (pos.average_cost - mark)
                    / pos.average_cost
                )
            else:  # long
                pnl_pct = (
                    (mark - pos.average_cost)
                    / pos.average_cost
                )
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

    # Mark order as exited so it won't be
    # picked up again by subsequent exit loops
    meta["exit_reason"] = reason
    meta["exit_time"] = (
        datetime.now(UTC).isoformat()
    )
    meta["exit_order_id"] = (
        status.client_order_id
    )
    meta["exited"] = True
    order.metadata_json = meta
    # Keep status as "filled" — the exited flag in
    # metadata is sufficient for exit-loop filtering

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
