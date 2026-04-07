"""Broker adapter registry.

Layer 2: Mode-aware adapter resolution.
Each execution mode maps to a fixed set of allowed adapters.
"""

from backend.adapters.broker.base import BrokerAdapter
from backend.adapters.broker.mock_broker import MockBrokerAdapter
from backend.core.execution_mode import ExecutionMode

# Mode → allowed adapter types
_MODE_ADAPTER_MAP: dict[ExecutionMode, list[str]] = {
    ExecutionMode.REPLAY: ["mock_paper_v1", "replay_v1"],
    ExecutionMode.SHADOW: ["mock_paper_v1", "shadow_v1"],
    ExecutionMode.PAPER: [
        "mock_paper_v1",
        "alpaca_paper_v1",
    ],
    ExecutionMode.MICRO_LIVE: [],  # Future: live adapters
    ExecutionMode.LIVE: [],  # Future: live adapters
}


def get_broker_adapter(mode: ExecutionMode) -> BrokerAdapter:
    """Get the appropriate broker adapter for the mode.

    Layer 2 safety: mode determines which adapter is used.
    """
    if mode in (ExecutionMode.REPLAY, ExecutionMode.SHADOW):
        return MockBrokerAdapter()

    if mode == ExecutionMode.PAPER:
        from backend.config.settings import settings
        if settings.alpaca_api_key:
            from backend.adapters.broker.alpaca_broker import (
                AlpacaPaperBrokerAdapter,
            )
            return AlpacaPaperBrokerAdapter()
        return MockBrokerAdapter()

    if mode in (ExecutionMode.MICRO_LIVE, ExecutionMode.LIVE):
        raise RuntimeError(
            f"No live broker adapter configured for "
            f"mode '{mode.value}'. "
            f"Register a live adapter first."
        )

    raise RuntimeError(f"Unknown execution mode: {mode.value}")


def validate_adapter_for_mode(
    adapter: BrokerAdapter, mode: ExecutionMode
) -> None:
    """Verify that an adapter is allowed for the given mode."""
    allowed = _MODE_ADAPTER_MAP.get(mode, [])
    if adapter.adapter_code not in allowed:
        raise RuntimeError(
            f"Adapter '{adapter.adapter_code}' is not "
            f"allowed for mode '{mode.value}'. "
            f"Allowed: {allowed}"
        )
