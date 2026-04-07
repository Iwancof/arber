"""Watch planner service.

Auto-generates watch plans for active market profiles
based on registered instruments and source bundles.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.sources import (
    SourceRegistry,
    WatchPlan,
    WatchPlanItem,
)

logger = logging.getLogger("eos.watch_planner")


async def generate_watch_plan(
    db: AsyncSession,
    *,
    market_profile_id: UUID,
    execution_mode: str = "paper",
) -> WatchPlan | None:
    """Generate a watch plan for a market profile.

    Creates a plan with all active sources assigned
    to the market.
    """
    # Get active sources for this market
    sources_result = await db.execute(
        select(SourceRegistry).where(
            SourceRegistry.status == "active",
        )
    )
    sources = list(sources_result.scalars().all())
    if not sources:
        logger.warning("No active sources")
        return None

    # Deactivate old plans
    old_plans = await db.execute(
        select(WatchPlan).where(
            WatchPlan.market_profile_id
            == market_profile_id,
            WatchPlan.active.is_(True),
        )
    )
    for old in old_plans.scalars().all():
        old.active = False

    # Create new plan
    plan = WatchPlan(
        market_profile_id=market_profile_id,
        execution_mode=execution_mode,
        generated_by="auto_planner",
        plan_reason_codes_json=["scheduled"],
    )
    db.add(plan)
    await db.flush()

    # Add items
    for i, src in enumerate(sources):
        item = WatchPlanItem(
            watch_plan_id=plan.watch_plan_id,
            source_id=src.source_id,
            priority=100 - i * 10,
            state="planned",
        )
        db.add(item)

    await db.commit()
    await db.refresh(plan)

    logger.info(
        "Watch plan generated: %d sources",
        len(sources),
    )
    return plan
