"""CLI entry point for the pipeline worker."""

import asyncio
import logging
import sys
from uuid import UUID

from backend.workers.pipeline import PipelineWorker


def main() -> None:
    """Run the pipeline worker from CLI."""
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s %(name)s %(levelname)s "
            "%(message)s"
        ),
    )

    # Parse simple args
    symbols = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    ]
    interval = 300
    market_id = None

    for arg in sys.argv[1:]:
        if arg.startswith("--symbols="):
            symbols = arg.split("=", 1)[1].split(
                ","
            )
        elif arg.startswith("--interval="):
            interval = int(
                arg.split("=", 1)[1]
            )
        elif arg.startswith("--market-id="):
            market_id = UUID(
                arg.split("=", 1)[1]
            )

    worker = PipelineWorker(
        fetch_interval_sec=interval,
        symbols=symbols,
        market_profile_id=market_id,
    )

    try:
        asyncio.run(worker.run_loop())
    except KeyboardInterrupt:
        worker.stop()


if __name__ == "__main__":
    main()
