"""Shared test fixtures for Event Intelligence OS."""

import pytest
from backend.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    """Async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
