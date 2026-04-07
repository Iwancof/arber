"""Tests for outbox and trace infrastructure."""

from backend.core.trace import (
    TraceContext,
    _trace_ctx,
    get_trace,
    new_trace,
    set_trace,
)


def test_trace_context_default():
    """New TraceContext should have a trace_id."""
    ctx = TraceContext()
    assert ctx.trace_id is not None
    assert len(ctx.trace_id) == 32  # hex UUID


def test_trace_context_unique():
    """Each TraceContext gets a unique trace_id."""
    a = TraceContext()
    b = TraceContext()
    assert a.trace_id != b.trace_id


def test_trace_context_child():
    """Child context should inherit trace_id."""
    parent = TraceContext()
    child = parent.child(causation_id="cause-123")
    assert child.trace_id == parent.trace_id
    assert child.causation_id == "cause-123"


def test_trace_context_child_default_causation():
    """Child without causation uses parent trace_id."""
    parent = TraceContext()
    child = parent.child()
    assert child.trace_id == parent.trace_id
    assert child.causation_id == parent.trace_id


def test_trace_context_child_correlation():
    """Child inherits correlation_id from parent."""
    parent = TraceContext(correlation_id="corr-1")
    child = parent.child()
    assert child.correlation_id == "corr-1"


def test_trace_context_child_correlation_fallback():
    """Child uses parent trace_id as correlation if none."""
    parent = TraceContext()
    child = parent.child()
    assert child.correlation_id == parent.trace_id


def test_new_trace_sets_context():
    """new_trace should set the context var."""
    ctx = new_trace()
    retrieved = get_trace()
    assert retrieved.trace_id == ctx.trace_id


def test_new_trace_with_correlation():
    """new_trace with correlation_id propagates it."""
    ctx = new_trace(correlation_id="my-corr")
    assert ctx.correlation_id == "my-corr"


def test_set_and_get_trace():
    """set_trace/get_trace should round-trip."""
    ctx = TraceContext(trace_id="abc123")
    set_trace(ctx)
    assert get_trace().trace_id == "abc123"


def test_get_trace_creates_if_missing():
    """get_trace should create a context if none set."""
    _trace_ctx.set(None)
    ctx = get_trace()
    assert ctx is not None
    assert ctx.trace_id is not None
    assert len(ctx.trace_id) == 32


def test_trace_context_explicit_id():
    """TraceContext with explicit trace_id uses it."""
    ctx = TraceContext(trace_id="explicit-id")
    assert ctx.trace_id == "explicit-id"
