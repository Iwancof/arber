"""Tests for API route registration."""

from backend.api.v1.router import api_v1_router


def test_all_expected_routes_registered():
    """V1 router should contain all Phase 1 routes."""
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


def test_route_count():
    """Should have 21 routes registered."""
    assert len(api_v1_router.routes) == 21
