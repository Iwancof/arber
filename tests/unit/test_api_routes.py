"""Tests for API route registration."""

from backend.api.v1.router import api_v1_router


def test_all_expected_routes_registered():
    """V1 router should contain all Phase 1-4 routes."""
    paths = [
        route.path for route in api_v1_router.routes
    ]
    # Health
    assert "/v1/health" in paths
    # Markets
    assert "/v1/markets" in paths
    assert "/v1/markets/{market_code}" in paths
    # Instruments
    assert "/v1/instruments" in paths
    assert "/v1/instruments/{instrument_id}" in paths
    # Sources
    assert "/v1/source-registry" in paths
    assert "/v1/source-registry/{source_code}" in paths
    # Events
    assert "/v1/events" in paths
    assert "/v1/events/{event_id}" in paths
    # Ingest
    assert "/v1/ingest/documents" in paths
    # Source candidates
    assert "/v1/source-candidates" in paths
    # Phase 2: Forecasts
    assert "/v1/forecasts" in paths
    assert "/v1/forecasts/{forecast_id}" in paths
    # Phase 2: Decisions
    assert "/v1/decisions" in paths
    assert "/v1/decisions/{decision_id}" in paths
    # Phase 2: Overlays
    assert "/v1/overlays/{instrument_id}" in paths
    # Phase 3: Postmortems
    assert "/v1/postmortems" in paths
    assert "/v1/postmortems/{postmortem_id}" in paths
    # Phase 3: Outcomes
    assert "/v1/outcomes/{forecast_id}" in paths
    # Phase 3: Prompt tasks
    assert "/v1/prompt-tasks" in paths
    assert "/v1/prompt-tasks/{task_id}" in paths
    assert (
        "/v1/prompt-tasks/{task_id}/make-visible"
        in paths
    )
    assert (
        "/v1/prompt-tasks/{task_id}/responses"
        in paths
    )
    # Phase 3: Replay jobs
    assert "/v1/replay-jobs" in paths
    assert "/v1/replay-jobs/{job_id}" in paths
    assert "/v1/replay-jobs/{job_id}/run" in paths
    # Phase 4: Orders
    assert "/v1/orders" in paths
    assert "/v1/orders/{order_id}" in paths
    assert "/v1/orders/{order_id}/fills" in paths
    # Phase 4: Positions
    assert "/v1/positions" in paths
    # Phase 4: Kill switches
    assert "/v1/kill-switches" in paths
    assert "/v1/kill-switches/activate" in paths
    assert (
        "/v1/kill-switches/{kill_switch_id}/clear"
        in paths
    )


def test_route_count():
    """Should have 46 routes registered."""
    assert len(api_v1_router.routes) == 46


def _all_methods_for(path: str) -> set[str]:
    """Collect all HTTP methods for a given path."""
    methods: set[str] = set()
    for route in api_v1_router.routes:
        if route.path == path and hasattr(route, "methods"):
            methods.update(route.methods)
    return methods


def test_prompt_task_routes_methods():
    """Prompt task routes should have correct methods."""
    pt = _all_methods_for("/v1/prompt-tasks")
    assert "GET" in pt
    assert "POST" in pt
    vis = _all_methods_for(
        "/v1/prompt-tasks/{task_id}/make-visible",
    )
    assert "POST" in vis


def test_replay_routes_methods():
    """Replay job routes should have correct methods."""
    rj = _all_methods_for("/v1/replay-jobs")
    assert "POST" in rj
    assert "GET" in rj
    run = _all_methods_for(
        "/v1/replay-jobs/{job_id}/run",
    )
    assert "POST" in run


def test_order_routes_methods():
    """Order routes should have correct methods."""
    orders = _all_methods_for("/v1/orders")
    assert "GET" in orders
    detail = _all_methods_for("/v1/orders/{order_id}")
    assert "GET" in detail
    fills = _all_methods_for(
        "/v1/orders/{order_id}/fills",
    )
    assert "GET" in fills


def test_position_routes_methods():
    """Position routes should have correct methods."""
    pos = _all_methods_for("/v1/positions")
    assert "GET" in pos


def test_kill_switch_routes_methods():
    """Kill switch routes should have correct methods."""
    ks = _all_methods_for("/v1/kill-switches")
    assert "GET" in ks
    activate = _all_methods_for(
        "/v1/kill-switches/activate",
    )
    assert "POST" in activate
    clear = _all_methods_for(
        "/v1/kill-switches/{kill_switch_id}/clear",
    )
    assert "POST" in clear
