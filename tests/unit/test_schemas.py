"""Tests for Pydantic API schemas."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from backend.schemas.common import PaginatedResponse
from backend.schemas.markets import InstrumentCreate, MarketProfileCreate, MarketProfileRead
from backend.schemas.sources import SourceRegistryCreate, SourceRegistryUpdate


def test_market_profile_create_defaults():
    """MarketProfileCreate should have correct defaults."""
    mp = MarketProfileCreate(
        market_code="US_EQUITY",
        display_name="US Equities",
        asset_class="equity",
        primary_timezone="America/New_York",
        quote_currency="USD",
        calendar_code="NYSE",
        session_template_json={"regular": {"start": "09:30", "end": "16:00"}},
    )
    assert mp.default_horizons_json == ["1d", "5d", "20d"]
    assert mp.enabled_execution_modes_json == ["replay", "shadow", "paper", "micro_live"]


def test_market_profile_read_from_dict():
    """MarketProfileRead should parse from dict (ORM mode)."""
    now = datetime.now(tz=UTC)
    data = {
        "market_profile_id": uuid4(),
        "market_code": "JP_EQUITY",
        "display_name": "Japan Equities",
        "asset_class": "equity",
        "primary_timezone": "Asia/Tokyo",
        "quote_currency": "JPY",
        "calendar_code": "TSE",
        "session_template_json": {},
        "default_horizons_json": ["1d"],
        "default_risk_rules_json": {},
        "enabled_execution_modes_json": ["replay"],
        "active": True,
        "created_at": now,
    }
    mp = MarketProfileRead(**data)
    assert mp.market_code == "JP_EQUITY"
    assert mp.active is True


def test_source_registry_create():
    """SourceRegistryCreate should validate correctly."""
    src = SourceRegistryCreate(
        source_code="sec_edgar",
        display_name="SEC EDGAR",
        source_type="official",
        adapter_type="json_api",
        trust_tier="official",
        latency_class="delayed",
    )
    assert src.retention_days == 365
    assert src.coverage_tags_json == []


def test_source_registry_update_partial():
    """SourceRegistryUpdate should allow partial updates."""
    update = SourceRegistryUpdate(display_name="Updated Name")
    dumped = update.model_dump(exclude_unset=True)
    assert dumped == {"display_name": "Updated Name"}


def test_instrument_create():
    """InstrumentCreate should validate correctly."""
    inst = InstrumentCreate(
        market_profile_id=uuid4(),
        symbol="AAPL",
        display_name="Apple Inc.",
        instrument_type="equity",
        quote_currency="USD",
    )
    assert inst.lot_size == Decimal("1")
    assert inst.metadata_json == {}


def test_paginated_response():
    """PaginatedResponse should include pagination fields."""
    resp = PaginatedResponse(total=100, limit=50, offset=0)
    assert resp.total == 100
