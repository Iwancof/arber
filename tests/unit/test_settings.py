"""Tests for application settings."""

from backend.config.settings import Settings


def test_default_settings():
    """Default settings should have expected values."""
    s = Settings()
    assert s.app_name == "Event Intelligence OS"
    assert s.app_version == "0.1.0"
    assert s.execution_mode == "replay"
    assert s.port == 50000
