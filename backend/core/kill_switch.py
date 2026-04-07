"""Kill switch types and checking logic.

Kill switches are scoped: observation, decision, and execution
are controlled independently.

Types:
- TRADE_HALT_GLOBAL: Block new risk orders, allow cancel/reduce
- REDUCE_ONLY_GLOBAL: Block new positions, allow close/reduce
- DECISION_HALT: Force all decisions to no_trade
- SOURCE_INGEST_PAUSE: Per-source ingest pause (scope_key = source_id)
- FULL_FREEZE: Emergency - halt decisions + orders
"""

from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.ops import KillSwitch


class KillSwitchType(StrEnum):
    """Kill switch types with different scopes."""

    TRADE_HALT_GLOBAL = "trade_halt_global"
    REDUCE_ONLY_GLOBAL = "reduce_only_global"
    DECISION_HALT = "decision_halt"
    SOURCE_INGEST_PAUSE = "source_ingest_pause"
    FULL_FREEZE = "full_freeze"


async def is_kill_active(
    db: AsyncSession,
    switch_type: KillSwitchType,
    scope_key: str = "all",
) -> KillSwitch | None:
    """Check if a specific kill switch type is active."""
    result = await db.execute(
        select(KillSwitch).where(
            KillSwitch.scope_type == switch_type.value,
            KillSwitch.scope_key == scope_key,
            KillSwitch.active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def check_trade_allowed(
    db: AsyncSession,
    *,
    side: str = "buy",
) -> None:
    """Check if new trades are allowed.

    Raises RuntimeError if blocked by any trade-related kill switch.
    """
    # Full freeze blocks everything
    freeze = await is_kill_active(db, KillSwitchType.FULL_FREEZE)
    if freeze:
        raise RuntimeError(f"FULL_FREEZE active: {freeze.reason}")

    # Trade halt blocks all new orders
    halt = await is_kill_active(db, KillSwitchType.TRADE_HALT_GLOBAL)
    if halt:
        raise RuntimeError(f"TRADE_HALT active: {halt.reason}")

    # Reduce-only blocks new positions (buys)
    if side == "buy":
        reduce = await is_kill_active(
            db, KillSwitchType.REDUCE_ONLY_GLOBAL
        )
        if reduce:
            raise RuntimeError(
                f"REDUCE_ONLY active: {reduce.reason}. "
                f"Only sell/reduce orders allowed."
            )


async def check_decision_allowed(db: AsyncSession) -> bool:
    """Check if decision engine should produce decisions.

    Returns False if decisions should be forced to no_trade.
    """
    freeze = await is_kill_active(db, KillSwitchType.FULL_FREEZE)
    if freeze:
        return False

    halt = await is_kill_active(db, KillSwitchType.DECISION_HALT)
    return not halt


async def check_source_ingest_allowed(
    db: AsyncSession,
    *,
    source_id: str,
) -> bool:
    """Check if a source is allowed to ingest.

    Returns False if source ingest is paused (per-source or global freeze).
    """
    # Check source-specific pause
    paused = await is_kill_active(
        db,
        KillSwitchType.SOURCE_INGEST_PAUSE,
        scope_key=source_id,
    )
    if paused:
        return False

    # Full freeze also pauses ingest
    freeze = await is_kill_active(db, KillSwitchType.FULL_FREEZE)
    return not freeze
