"""Tests for API route registration."""

from backend.api.v1.router import api_v1_router


def test_all_expected_routes_registered():
    """V1 router should contain all Phase 1 and Phase 2 routes."""
    paths = [route.path for route in api_v1_router.routes]
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


def test_route_count():
    """Should have 26 routes registered."""
    assert len(api_v1_router.routes) == 26
