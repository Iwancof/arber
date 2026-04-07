"""Trace context for request/event correlation.

Provides trace_id, correlation_id, causation_id propagation.
"""

import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field

_trace_ctx: ContextVar["TraceContext | None"] = ContextVar(
    "trace_ctx", default=None
)


@dataclass
class TraceContext:
    """Immutable trace context for a request/event flow."""
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    correlation_id: str | None = None
    causation_id: str | None = None

    def child(self, causation_id: str | None = None) -> "TraceContext":
        """Create a child context with same trace, new causation."""
        return TraceContext(
            trace_id=self.trace_id,
            correlation_id=self.correlation_id or self.trace_id,
            causation_id=causation_id or self.trace_id,
        )


def get_trace() -> TraceContext:
    """Get current trace context, creating one if needed."""
    ctx = _trace_ctx.get()
    if ctx is None:
        ctx = TraceContext()
        _trace_ctx.set(ctx)
    return ctx


def set_trace(ctx: TraceContext) -> None:
    """Set the trace context for the current async context."""
    _trace_ctx.set(ctx)


def new_trace(
    *, correlation_id: str | None = None
) -> TraceContext:
    """Create and set a new trace context."""
    ctx = TraceContext(correlation_id=correlation_id)
    _trace_ctx.set(ctx)
    return ctx
