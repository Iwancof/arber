"""Execution mode definitions and safety guards.

Execution modes are fail-closed: misconfiguration cannot
accidentally reach live trading.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class ExecutionMode(StrEnum):
    """Execution modes with strict ordering."""
    REPLAY = "replay"
    SHADOW = "shadow"
    PAPER = "paper"
    MICRO_LIVE = "micro_live"
    LIVE = "live"

    @property
    def allows_broker_submission(self) -> bool:
        """Whether this mode can submit real/paper orders."""
        return self in (
            ExecutionMode.PAPER,
            ExecutionMode.MICRO_LIVE,
            ExecutionMode.LIVE,
        )

    @property
    def is_live(self) -> bool:
        """Whether this mode uses real money."""
        return self in (ExecutionMode.MICRO_LIVE, ExecutionMode.LIVE)

    @property
    def requires_arming(self) -> bool:
        """Whether this mode requires explicit arming."""
        return self.is_live


@dataclass
class LiveArmingState:
    """Tracks whether live trading is armed."""
    armed: bool = False
    armed_until: datetime | None = None
    armed_by: str | None = None
    reason: str | None = None

    @property
    def is_armed(self) -> bool:
        if not self.armed:
            return False
        return not (
            self.armed_until and datetime.now(UTC) > self.armed_until
        )


# Global arming state (in production, this would be in DB/Redis)
_live_arming = LiveArmingState()


def get_live_arming() -> LiveArmingState:
    return _live_arming


def arm_live(
    *, armed_by: str, reason: str, armed_until: datetime
) -> LiveArmingState:
    """Arm live trading with a TTL."""
    global _live_arming
    _live_arming = LiveArmingState(
        armed=True,
        armed_until=armed_until,
        armed_by=armed_by,
        reason=reason,
    )
    return _live_arming


def disarm_live() -> LiveArmingState:
    """Disarm live trading."""
    global _live_arming
    _live_arming = LiveArmingState()
    return _live_arming


def validate_mode_for_order_submission(mode: ExecutionMode) -> None:
    """Layer 1: Service-level mode guard.

    Raises RuntimeError if mode does not allow order submission.
    """
    if not mode.allows_broker_submission:
        raise RuntimeError(
            f"Execution mode '{mode.value}' does not allow "
            f"broker order submission. "
            f"Use paper/micro_live/live modes."
        )

    if mode.requires_arming and not get_live_arming().is_armed:
        raise RuntimeError(
            f"Live trading is not armed. "
            f"Call arm_live() before submitting "
            f"'{mode.value}' orders."
        )
