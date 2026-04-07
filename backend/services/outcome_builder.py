"""Outcome builder service.

Evaluates forecast accuracy by fetching realized market
returns from Alpaca and computing relative performance.
Runs periodically to check which forecast horizons have
matured and need outcome records.
"""

import hashlib
import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.source.alpaca_market_data import (
    AlpacaMarketDataAdapter,
)
from backend.core.outbox import emit_event
from backend.models.core import Instrument
from backend.models.feedback import (
    OutcomeLedger,
    ReliabilityStat,
)
from backend.models.forecasting import (
    ForecastHorizon,
    ForecastLedger,
)

logger = logging.getLogger("eos.outcome")

# Horizon code -> trading days
HORIZON_DAYS = {"1d": 1, "5d": 5, "20d": 20}
# Default benchmark
DEFAULT_BENCHMARK = "SPY"


async def check_matured_forecasts(
    db: AsyncSession,
) -> int:
    """Find forecasts whose horizon has matured and
    build outcomes for them.

    Returns number of outcomes created.
    """
    mkt = AlpacaMarketDataAdapter()
    now = datetime.now(UTC)
    created = 0

    # Find forecast horizons without outcomes
    result = await db.execute(
        select(
            ForecastHorizon,
            ForecastLedger,
        )
        .join(
            ForecastLedger,
            ForecastLedger.forecast_id
            == ForecastHorizon.forecast_id,
        )
        .outerjoin(
            OutcomeLedger,
            (
                OutcomeLedger.forecast_id
                == ForecastHorizon.forecast_id
            )
            & (
                OutcomeLedger.horizon_code
                == ForecastHorizon.horizon_code
            ),
        )
        .where(
            OutcomeLedger.outcome_id.is_(None),
            ForecastLedger.forecasted_at.isnot(None),
        )
    )
    rows = result.all()

    for horizon, forecast in rows:
        days = HORIZON_DAYS.get(
            horizon.horizon_code, 5
        )
        maturity = forecast.forecasted_at + timedelta(
            days=days + 1  # buffer for market close
        )
        if now < maturity:
            continue

        # Get instrument symbol
        inst_result = await db.execute(
            select(Instrument.symbol).where(
                Instrument.instrument_id
                == forecast.instrument_id
            )
        )
        symbol = inst_result.scalar_one_or_none()
        if not symbol:
            continue

        try:
            outcome = await build_single_outcome(
                db,
                mkt,
                forecast=forecast,
                horizon=horizon,
                symbol=symbol,
            )
            if outcome:
                created += 1
        except Exception:
            logger.exception(
                "Outcome build failed for %s/%s",
                symbol,
                horizon.horizon_code,
            )

    return created


async def build_single_outcome(
    db: AsyncSession,
    mkt: AlpacaMarketDataAdapter,
    *,
    forecast: ForecastLedger,
    horizon: ForecastHorizon,
    symbol: str,
) -> OutcomeLedger | None:
    """Build one outcome for a forecast+horizon."""
    days = HORIZON_DAYS.get(
        horizon.horizon_code, 5
    )
    start = forecast.forecasted_at - timedelta(
        days=1
    )
    end = forecast.forecasted_at + timedelta(
        days=days + 2
    )

    # Get stock bars
    bars = await mkt.get_daily_bars(
        symbol,
        start=start,
        end=end,
        limit=days + 5,
    )
    if len(bars) < 2:
        logger.warning(
            "Not enough bars for %s", symbol
        )
        return None

    # Get benchmark bars
    bench_bars = await mkt.get_daily_bars(
        DEFAULT_BENCHMARK,
        start=start,
        end=end,
        limit=days + 5,
    )

    # Compute returns
    entry_price = Decimal(
        str(bars[0].get("c", 0))
    )
    exit_price = Decimal(
        str(bars[-1].get("c", 0))
    )
    if entry_price == 0:
        return None

    abs_return = (
        (exit_price - entry_price) / entry_price
    )

    # Benchmark return
    bench_return = Decimal("0")
    if len(bench_bars) >= 2:
        b_entry = Decimal(
            str(bench_bars[0].get("c", 0))
        )
        b_exit = Decimal(
            str(bench_bars[-1].get("c", 0))
        )
        if b_entry > 0:
            bench_return = (
                (b_exit - b_entry) / b_entry
            )

    rel_return = abs_return - bench_return

    # Check barrier
    p_down = horizon.p_downside_barrier
    barrier_hit = False
    if p_down and p_down > Decimal("0"):
        for bar in bars[1:]:
            low = Decimal(str(bar.get("l", 0)))
            thresh = entry_price * (1 - p_down)
            if low < thresh:
                barrier_hit = True
                break

    # Horizon end
    horizon_end = (
        forecast.forecasted_at
        + timedelta(days=days)
    )

    outcome = OutcomeLedger(
        forecast_id=forecast.forecast_id,
        horizon_code=horizon.horizon_code,
        horizon_end_at=horizon_end,
        realized_abs_return=abs_return,
        realized_rel_return=rel_return,
        benchmark_return=bench_return,
        barrier_hit=barrier_hit,
        outcome_json={
            "symbol": symbol,
            "benchmark": DEFAULT_BENCHMARK,
            "entry_price": str(entry_price),
            "exit_price": str(exit_price),
            "bars_count": len(bars),
        },
    )
    db.add(outcome)
    await db.flush()  # populate outcome_id

    await emit_event(
        db,
        event_type="created",
        aggregate_type="outcome",
        aggregate_id=str(outcome.outcome_id),
        payload={
            "forecast_id": str(
                forecast.forecast_id
            ),
            "horizon": horizon.horizon_code,
            "rel_return": str(rel_return),
        },
    )

    await db.commit()
    await db.refresh(outcome)

    logger.info(
        "Outcome: %s %s rel=%.4f%% abs=%.4f%%",
        symbol,
        horizon.horizon_code,
        float(rel_return * 100),
        float(abs_return * 100),
    )
    return outcome


async def update_reliability_stats(
    db: AsyncSession,
) -> int:
    """Update reliability stats from outcomes.

    Computes hit rate, brier score per dimension.
    """
    # Get outcomes with forecasts
    result = await db.execute(
        select(
            OutcomeLedger,
            ForecastLedger,
            ForecastHorizon,
        )
        .join(
            ForecastLedger,
            ForecastLedger.forecast_id
            == OutcomeLedger.forecast_id,
        )
        .join(
            ForecastHorizon,
            (
                ForecastHorizon.forecast_id
                == OutcomeLedger.forecast_id
            )
            & (
                ForecastHorizon.horizon_code
                == OutcomeLedger.horizon_code
            ),
        )
    )
    rows = result.all()

    # Group by dimension
    dims: dict[str, list] = defaultdict(list)

    for outcome, forecast, horizon in rows:
        key = (
            f"{forecast.market_profile_id}:"
            f"{horizon.horizon_code}:"
            f"{forecast.model_family}"
        )
        p_out = float(
            horizon.p_outperform_benchmark or 0.5
        )
        actual = (
            float(
                outcome.realized_rel_return or 0
            )
            > 0
        )
        dims[key].append((p_out, actual))

    updated = 0
    for dim_key, samples in dims.items():
        n = len(samples)
        if n < 2:
            continue

        hits = sum(
            1
            for p, a in samples
            if (p > 0.5) == a
        )
        hit_rate = Decimal(str(hits / n))

        # Brier score
        brier = sum(
            (p - (1.0 if a else 0.0)) ** 2
            for p, a in samples
        ) / n
        brier_dec = Decimal(str(brier))

        dim_hash = hashlib.sha256(
            dim_key.encode()
        ).hexdigest()[:32]

        # Upsert
        existing = await db.execute(
            select(ReliabilityStat).where(
                ReliabilityStat.dimension_hash
                == dim_hash
            )
        )
        stat = existing.scalar_one_or_none()
        if stat:
            stat.sample_size = n
            stat.hit_rate = hit_rate
            stat.brier = brier_dec
            stat.last_validated_at = (
                datetime.now(UTC)
            )
        else:
            parts = dim_key.split(":")
            stat = ReliabilityStat(
                dimension_hash=dim_hash,
                horizon_code=(
                    parts[1]
                    if len(parts) > 1
                    else None
                ),
                model_family=(
                    parts[2]
                    if len(parts) > 2
                    else None
                ),
                sample_size=n,
                hit_rate=hit_rate,
                brier=brier_dec,
                last_validated_at=(
                    datetime.now(UTC)
                ),
                stats_json={
                    "dim_key": dim_key,
                },
            )
            db.add(stat)
        updated += 1

    if updated:
        await db.commit()
    logger.info(
        "Reliability updated: %d dimensions",
        updated,
    )
    return updated
