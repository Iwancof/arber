"""Tests for the ingest service."""

from backend.services.ingest import compute_content_hash


async def test_content_hash_deterministic():
    """Same content should produce same hash."""
    h1 = await compute_content_hash("test content")
    h2 = await compute_content_hash("test content")
    assert h1 == h2


async def test_content_hash_different_for_different_content():
    """Different content should produce different hashes."""
    h1 = await compute_content_hash("content A")
    h2 = await compute_content_hash("content B")
    assert h1 != h2


async def test_content_hash_is_sha256():
    """Hash should be 64 character hex string (SHA-256)."""
    h = await compute_content_hash("test")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)
