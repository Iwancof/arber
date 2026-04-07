"""Market profile and instrument schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from backend.schemas.common import OrmBase, PaginatedResponse


class MarketProfileRead(OrmBase):
    """Market profile response schema."""
    market_profile_id: UUID
    market_code: str
    display_name: str
    asset_class: str
    primary_timezone: str
    quote_currency: str
    calendar_code: str
    session_template_json: dict[str, Any]
    default_horizons_json: list[str]
    default_risk_rules_json: dict[str, Any]
    enabled_execution_modes_json: list[str]
    active: bool
    created_at: datetime


class MarketProfileCreate(OrmBase):
    """Market profile creation schema."""
    market_code: str
    display_name: str
    asset_class: str
    primary_timezone: str
    quote_currency: str
    calendar_code: str
    session_template_json: dict[str, Any]
    default_horizons_json: list[str] = ["1d", "5d", "20d"]
    default_risk_rules_json: dict[str, Any] = {}
    enabled_execution_modes_json: list[str] = ["replay", "shadow", "paper", "micro_live"]


class MarketProfileList(PaginatedResponse):
    """Paginated list of market profiles."""
    items: list[MarketProfileRead]


class InstrumentRead(OrmBase):
    """Instrument response schema."""
    instrument_id: UUID
    market_profile_id: UUID
    venue_id: UUID | None = None
    symbol: str
    display_name: str
    instrument_type: str
    quote_currency: str
    sector: str | None = None
    industry: str | None = None
    isin: str | None = None
    lot_size: Decimal
    active: bool
    metadata_json: dict[str, Any]
    created_at: datetime


class InstrumentCreate(OrmBase):
    """Instrument creation schema."""
    market_profile_id: UUID
    venue_id: UUID | None = None
    symbol: str
    display_name: str
    instrument_type: str
    quote_currency: str
    sector: str | None = None
    industry: str | None = None
    isin: str | None = None
    cusip: str | None = None
    figi: str | None = None
    lot_size: Decimal = Decimal("1")
    metadata_json: dict[str, Any] = {}


class InstrumentList(PaginatedResponse):
    """Paginated list of instruments."""
    items: list[InstrumentRead]
