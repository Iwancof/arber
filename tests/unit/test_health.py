"""Tests for health check endpoint."""

import pytest


@pytest.mark.asyncio
async def test_health_endpoint_returns_response(client):
    """Health endpoint should return a JSON response."""
    response = await client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
