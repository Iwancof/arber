"""Background pipeline worker.

Orchestrates: fetch -> ingest -> extract -> forecast -> decide.
Runs as an asyncio loop with configurable intervals.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.source.alpaca_news import (
    AlpacaNewsAdapter,
)
from backend.adapters.source.boj_rss import (
    BOJRSSAdapter,
)
from backend.adapters.worker.registry import (
    get_worker_adapter,
)
from backend.config.settings import settings
from backend.core.trace import new_trace
from backend.db.session import async_session_factory
from backend.models.content import EventLedger, RawDocument
from backend.models.core import Instrument
from backend.services.decision import evaluate_forecast
from backend.services.forecast import run_forecast_pipeline
from backend.services.ingest import ingest_document

logger = logging.getLogger("eos.pipeline")


def _parse_datetime(s: str) -> datetime:
    """Parse datetime from various formats."""
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        pass
    # RFC 2822 (e.g. BOJ RSS)
    from email.utils import parsedate_to_datetime
    try:
        return parsedate_to_datetime(s)
    except Exception:
        pass
    return datetime.now(UTC)


class PipelineWorker:
    """Background worker running the full pipeline."""

    def __init__(
        self,
        *,
        fetch_interval_sec: int = 300,
        symbols: list[str] | None = None,
        market_profile_id: UUID | None = None,
    ) -> None:
        self._fetch_interval = fetch_interval_sec
        self._symbols = symbols or []
        self._market_profile_id = market_profile_id
        self._news = AlpacaNewsAdapter()
        self._boj = BOJRSSAdapter()
        self._worker = get_worker_adapter()
        self._running = False
        self._jp_market_id: UUID | None = None

    async def run_once(self) -> dict[str, int]:
        """Run one full pipeline cycle.

        Returns counts of processed items.
        """
        ctx = new_trace()
        logger.info(
            "Pipeline cycle start [trace=%s]",
            ctx.trace_id,
        )

        stats: dict[str, int] = {
            "fetched": 0,
            "ingested": 0,
            "noise_filtered": 0,
            "extracted": 0,
            "forecasted": 0,
            "decided": 0,
            "errors": 0,
        }

        async with async_session_factory() as db:
            # Step 1: Fetch news
            try:
                articles = await self._news.fetch(
                    symbols=self._symbols,
                    start=datetime.now(UTC)
                    - timedelta(hours=1),
                    limit=20,
                )
                stats["fetched"] = len(articles)
                logger.info(
                    "Fetched %d articles",
                    len(articles),
                )
            except Exception:
                logger.exception("News fetch failed")
                stats["errors"] += 1
                articles = []

            # Step 1b: Fetch JP news (BOJ)
            try:
                jp_articles = await self._boj.fetch(
                    limit=5
                )
                articles.extend(jp_articles)
                stats["fetched"] = len(articles)
                if jp_articles:
                    logger.info(
                        "JP: +%d BOJ articles",
                        len(jp_articles),
                    )
            except Exception:
                logger.exception(
                    "BOJ fetch failed"
                )

            if not articles:
                return stats

            # Step 2: Ingest documents
            source_id = await self._get_source_id(db)
            jp_source_id = await self._get_jp_source_id(
                db
            )

            docs: list[RawDocument] = []
            for article in articles:
                lang = article.get(
                    "language_code", "en"
                )
                sid = (
                    jp_source_id
                    if lang == "ja" and jp_source_id
                    else source_id
                )
                if not sid:
                    continue
                try:
                    doc = await ingest_document(
                        db,
                        source_id=sid,
                        headline=article.get(
                            "headline"
                        ),
                        url=article.get("url"),
                        raw_text=article.get(
                            "raw_text"
                        ),
                        raw_payload_json=article.get(
                            "raw_payload_json", {}
                        ),
                        published_at=(
                            _parse_datetime(
                                article["published_at"]
                            )
                        ),
                        language_code=article.get(
                            "language_code", "en"
                        ),
                        source_tier=article.get(
                            "source_tier",
                            "high_vendor",
                        ),
                        native_doc_id=article.get(
                            "native_doc_id"
                        ),
                    )
                    docs.append(doc)
                    stats["ingested"] += 1
                except Exception:
                    logger.exception(
                        "Ingest failed"
                    )
                    stats["errors"] += 1

            # Step 2.5: Noise gate (headline filter)
            signal_docs: list[RawDocument] = []
            for doc in docs:
                try:
                    is_signal = await self._noise_gate(
                        doc
                    )
                    if is_signal:
                        signal_docs.append(doc)
                    else:
                        stats["noise_filtered"] += 1
                except Exception:
                    # On error, let it through
                    signal_docs.append(doc)

            logger.info(
                "Noise gate: %d signal, %d noise",
                len(signal_docs),
                stats["noise_filtered"],
            )

            # Step 3: Extract events via LLM
            for doc in signal_docs:
                try:
                    event = (
                        await self._extract_event(
                            db, doc
                        )
                    )
                    if event:
                        stats["extracted"] += 1
                        await self._forecast_decide(
                            db, event, stats
                        )
                except Exception:
                    logger.exception(
                        "Pipeline step failed"
                    )
                    stats["errors"] += 1

        # Outcome builder: check matured forecasts
        try:
            from backend.services.outcome_builder import (
                check_matured_forecasts,
                update_reliability_stats,
            )
            async with (
                async_session_factory() as outcome_db
            ):
                outcomes = (
                    await check_matured_forecasts(
                        outcome_db
                    )
                )
                if outcomes:
                    await update_reliability_stats(
                        outcome_db
                    )
                    logger.info(
                        "Outcomes built: %d",
                        outcomes,
                    )
        except Exception:
            logger.exception(
                "Outcome builder error"
            )

        # Exit engine: check time and stop exits
        if settings.execution_mode == "paper":
            try:
                from backend.adapters.broker.registry import (
                    get_broker_adapter,
                )
                from backend.core.execution_mode import (
                    ExecutionMode,
                )
                from backend.services.exit_engine import (
                    check_stop_exits,
                    check_time_exits,
                )
                broker = get_broker_adapter(
                    ExecutionMode.PAPER
                )
                async with (
                    async_session_factory() as exit_db
                ):
                    time_exits = (
                        await check_time_exits(
                            exit_db, broker
                        )
                    )
                    stop_exits = (
                        await check_stop_exits(
                            exit_db, broker
                        )
                    )
                    if time_exits or stop_exits:
                        logger.info(
                            "Exits: time=%d "
                            "stop=%d",
                            time_exits,
                            stop_exits,
                        )
            except Exception:
                logger.exception(
                    "Exit engine error"
                )

        logger.info(
            "Pipeline cycle done: %s", stats
        )
        return stats

    async def _forecast_decide(
        self,
        db: AsyncSession,
        event: EventLedger,
        stats: dict[str, int],
    ) -> None:
        """Steps 4+5: Forecast and Decision."""
        if not (
            event.issuer_instrument_id
            and self._market_profile_id
        ):
            return

        forecast = await run_forecast_pipeline(
            db,
            self._worker,
            event_id=event.event_id,
            instrument_id=(
                event.issuer_instrument_id
            ),
            market_profile_id=(
                self._market_profile_id
            ),
            execution_mode=(
                settings.execution_mode
            ),
        )
        stats["forecasted"] += 1

        decision = await evaluate_forecast(
            db,
            forecast_id=forecast.forecast_id,
            execution_mode=(
                settings.execution_mode
            ),
        )
        stats["decided"] += 1

        if (
            decision.action == "long_candidate"
            and settings.execution_mode == "paper"
        ):
            from backend.adapters.broker.registry import (
                get_broker_adapter,
            )
            from backend.core.execution_mode import (
                ExecutionMode,
            )
            from backend.services.execution import (
                submit_order,
            )
            try:
                broker = get_broker_adapter(
                    ExecutionMode.PAPER
                )
                await submit_order(
                    db,
                    broker,
                    decision_id=(
                        decision.decision_id
                    ),
                    execution_mode="paper",
                )
                stats.setdefault("ordered", 0)
                stats["ordered"] = (
                    stats.get("ordered", 0) + 1
                )
            except Exception:
                logger.exception(
                    "Order submission failed"
                )
                stats["errors"] += 1

        # Inquiry signal evaluation
        try:
            from backend.services.inquiry_signal import (
                evaluate_decision_signals,
            )
            sigs = await evaluate_decision_signals(
                db, decision_id=decision.decision_id,
            )
            if sigs:
                stats.setdefault("signals", 0)
                stats["signals"] += len(sigs)
        except Exception:
            logger.exception("Signal evaluation failed")

    async def run_loop(self) -> None:
        """Run the pipeline continuously."""
        self._running = True
        logger.info(
            "Pipeline worker starting "
            "(interval=%ds, symbols=%s)",
            self._fetch_interval,
            self._symbols,
        )
        while self._running:
            try:
                await self.run_once()
            except Exception:
                logger.exception(
                    "Pipeline cycle error"
                )
            await asyncio.sleep(
                self._fetch_interval
            )

    def stop(self) -> None:
        """Stop the pipeline loop."""
        self._running = False
        logger.info("Pipeline worker stopping")

    async def _get_source_id(
        self, db: AsyncSession
    ) -> UUID | None:
        """Get the first active Alpaca source."""
        from backend.models.sources import (
            SourceRegistry,
        )

        result = await db.execute(
            select(
                SourceRegistry.source_id
            ).where(
                SourceRegistry.source_code.in_(
                    [
                        "alpaca_news",
                        "alpaca-news",
                    ]
                )
            )
        )
        row = result.scalar_one_or_none()
        return row

    async def _get_jp_source_id(
        self, db: AsyncSession
    ) -> UUID | None:
        """Get the first active JP source."""
        from backend.models.sources import (
            SourceRegistry,
        )

        result = await db.execute(
            select(
                SourceRegistry.source_id
            ).where(
                SourceRegistry.source_code.in_(
                    [
                        "boj_rss",
                        "jpx_disclosure",
                    ]
                )
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def _extract_event(
        self,
        db: AsyncSession,
        doc: RawDocument,
    ) -> EventLedger | None:
        """Extract a structured event."""
        from backend.adapters.worker.base import (
            WorkerTask,
        )

        # Language-aware task type
        lang = doc.language_code or "en"
        task_type = (
            "event_extract_ja"
            if lang == "ja"
            else "event_extract"
        )

        task = WorkerTask(
            task_type=task_type,
            schema_name="event_record",
            schema_version="1.0.0",
            prompt_template_id=task_type,
            prompt_version="1.0.0",
            input_payload={
                "headline": doc.headline or "",
                "raw_text": doc.raw_text or "",
                "url": doc.url or "",
                "source_tier": doc.source_tier,
            },
            evidence_refs=[
                str(doc.raw_document_id)
            ],
            mode=settings.execution_mode,
        )

        result = await self._worker.execute(task)

        if not result.schema_valid:
            logger.warning(
                "Event extract failed doc %s: %s",
                doc.raw_document_id,
                result.parse_errors,
            )
            return None

        events = result.parsed_json.get(
            "events", []
        )
        if not events:
            return None

        ev = events[0]  # Take first event

        # Resolve instrument (auto-register if new)
        lang = doc.language_code or "en"
        instrument_id = (
            await self._resolve_instrument(
                db,
                ev.get("affected_assets", []),
                language=lang,
            )
        )

        event = EventLedger(
            raw_document_id=doc.raw_document_id,
            event_type=ev.get(
                "event_type", "unknown"
            ),
            issuer_instrument_id=instrument_id,
            market_profile_id=(
                self._market_profile_id
            ),
            event_time=datetime.now(UTC),
            direction_hint=ev.get(
                "direction_hint"
            ),
            materiality=ev.get("materiality"),
            novelty=ev.get("novelty"),
            extraction_version="anthropic_v2",
            schema_version="1.0.0",
            event_json=ev,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    async def _noise_gate(
        self, doc: RawDocument
    ) -> bool:
        """Classify headline as signal or noise.

        Returns True if the doc should be processed.
        """
        from backend.adapters.worker.base import (
            WorkerTask,
        )

        task = WorkerTask(
            task_type="noise_classifier",
            schema_name="noise_classification",
            schema_version="1.0.0",
            input_payload={
                "headline": doc.headline or "",
            },
            mode=settings.execution_mode,
        )

        result = await self._worker.execute(task)
        if not result.schema_valid:
            return True  # On failure, let it through

        classification = result.parsed_json.get(
            "classification", "uncertain"
        )

        if classification == "noise":
            logger.info(
                "Noise filtered: %s",
                (doc.headline or "")[:60],
            )
            return False

        # signal or uncertain → process
        return True

    async def _resolve_instrument(
        self,
        db: AsyncSession,
        symbols: list[str],
        *,
        language: str = "en",
    ) -> UUID | None:
        """Resolve symbols to an instrument ID.

        Auto-registers unknown symbols if a market
        profile is configured.
        """
        if not symbols:
            return None

        # Try existing
        result = await db.execute(
            select(Instrument.instrument_id)
            .where(Instrument.symbol.in_(symbols))
            .limit(1)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        # Auto-register first symbol
        if not self._market_profile_id:
            return None

        sym = symbols[0]
        currency = "JPY" if language == "ja" else "USD"

        # Find appropriate market profile
        from backend.models.core import MarketProfile
        mp_result = await db.execute(
            select(MarketProfile.market_profile_id)
            .where(
                MarketProfile.quote_currency == currency
            )
            .limit(1)
        )
        mp_id = (
            mp_result.scalar_one_or_none()
            or self._market_profile_id
        )

        logger.info(
            "Auto-register: %s (%s)", sym, currency
        )
        instrument = Instrument(
            market_profile_id=mp_id,
            symbol=sym,
            display_name=sym,
            instrument_type="equity",
            quote_currency=currency,
        )
        db.add(instrument)
        await db.flush()
        return instrument.instrument_id
