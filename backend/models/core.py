"""SQLAlchemy ORM models for the core schema of Event Intelligence OS."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


# ---------------------------------------------------------------------------
# core.app_user
# ---------------------------------------------------------------------------
class AppUser(TimestampMixin, Base):
    __tablename__ = "app_user"
    __table_args__ = {"schema": "core"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default="active"
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # relationships
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        foreign_keys="UserRole.user_id",
    )


# ---------------------------------------------------------------------------
# core.role
# ---------------------------------------------------------------------------
class Role(Base):
    __tablename__ = "role"
    __table_args__ = {"schema": "core"}

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    role_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)

    # relationships
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="role"
    )


# ---------------------------------------------------------------------------
# core.user_role
# ---------------------------------------------------------------------------
class UserRole(Base):
    __tablename__ = "user_role"
    __table_args__ = {"schema": "core"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.app_user.user_id"),
        primary_key=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.role.role_id"),
        primary_key=True,
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.app_user.user_id"),
        nullable=True,
    )

    # relationships
    user: Mapped["AppUser"] = relationship(
        "AppUser", back_populates="user_roles", foreign_keys=[user_id]
    )
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")
    granter: Mapped[Optional["AppUser"]] = relationship(
        "AppUser", foreign_keys=[granted_by]
    )


# ---------------------------------------------------------------------------
# core.market_profile
# ---------------------------------------------------------------------------
class MarketProfile(TimestampMixin, Base):
    __tablename__ = "market_profile"
    __table_args__ = {"schema": "core"}

    market_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    market_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    asset_class: Mapped[str] = mapped_column(Text, nullable=False)
    primary_timezone: Mapped[str] = mapped_column(Text, nullable=False)
    quote_currency: Mapped[str] = mapped_column(Text, nullable=False)
    calendar_code: Mapped[str] = mapped_column(Text, nullable=False)

    session_template_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    default_horizons_json: Mapped[dict | None] = mapped_column(
        JSONB, server_default='["1d","5d","20d"]'
    )
    default_risk_rules_json: Mapped[dict | None] = mapped_column(
        JSONB, server_default="{}"
    )
    default_language_priority_json: Mapped[dict | None] = mapped_column(
        JSONB, server_default='["en"]'
    )
    default_source_bundle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    enabled_execution_modes_json: Mapped[dict | None] = mapped_column(
        JSONB, server_default='["replay","shadow","paper","micro_live"]'
    )
    active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)

    # relationships
    venues: Mapped[list["TradingVenue"]] = relationship(
        "TradingVenue", back_populates="market_profile"
    )
    instruments: Mapped[list["Instrument"]] = relationship(
        "Instrument", back_populates="market_profile"
    )


# ---------------------------------------------------------------------------
# core.trading_venue
# ---------------------------------------------------------------------------
class TradingVenue(Base):
    __tablename__ = "trading_venue"
    __table_args__ = (
        UniqueConstraint("market_profile_id", "venue_code"),
        {"schema": "core"},
    )

    venue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    market_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.market_profile.market_profile_id"),
        nullable=False,
    )
    venue_code: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    country_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)

    # relationships
    market_profile: Mapped["MarketProfile"] = relationship(
        "MarketProfile", back_populates="venues"
    )
    instruments: Mapped[list["Instrument"]] = relationship(
        "Instrument", back_populates="venue"
    )


# ---------------------------------------------------------------------------
# core.instrument
# ---------------------------------------------------------------------------
class Instrument(TimestampMixin, Base):
    __tablename__ = "instrument"
    __table_args__ = (
        UniqueConstraint("market_profile_id", "symbol"),
        {"schema": "core"},
    )

    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    market_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.market_profile.market_profile_id"),
        nullable=False,
    )
    venue_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.trading_venue.venue_id"),
        nullable=True,
    )
    symbol: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    instrument_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    quote_currency: Mapped[str | None] = mapped_column(Text, nullable=True)
    sector: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(Text, nullable=True)
    isin: Mapped[str | None] = mapped_column(Text, nullable=True)
    cusip: Mapped[str | None] = mapped_column(Text, nullable=True)
    figi: Mapped[str | None] = mapped_column(Text, nullable=True)
    lot_size: Mapped[Decimal] = mapped_column(
        Numeric(18, 6), server_default="1", nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB, server_default="{}"
    )

    # relationships
    market_profile: Mapped["MarketProfile"] = relationship(
        "MarketProfile", back_populates="instruments"
    )
    venue: Mapped[Optional["TradingVenue"]] = relationship(
        "TradingVenue", back_populates="instruments"
    )
    aliases: Mapped[list["InstrumentAlias"]] = relationship(
        "InstrumentAlias", back_populates="instrument"
    )
    benchmark_maps: Mapped[list["BenchmarkMap"]] = relationship(
        "BenchmarkMap",
        back_populates="instrument",
        foreign_keys="BenchmarkMap.instrument_id",
    )
    benchmark_of: Mapped[list["BenchmarkMap"]] = relationship(
        "BenchmarkMap",
        back_populates="benchmark_instrument",
        foreign_keys="BenchmarkMap.benchmark_instrument_id",
    )


# ---------------------------------------------------------------------------
# core.instrument_alias
# ---------------------------------------------------------------------------
class InstrumentAlias(Base):
    __tablename__ = "instrument_alias"
    __table_args__ = (
        UniqueConstraint("instrument_id", "alias_type", "alias_value"),
        {"schema": "core"},
    )

    alias_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.instrument.instrument_id"),
        nullable=False,
    )
    alias_type: Mapped[str] = mapped_column(Text, nullable=False)
    alias_value: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)

    # relationships
    instrument: Mapped["Instrument"] = relationship(
        "Instrument", back_populates="aliases"
    )


# ---------------------------------------------------------------------------
# core.benchmark_map
# ---------------------------------------------------------------------------
class BenchmarkMap(Base):
    __tablename__ = "benchmark_map"
    __table_args__ = (
        UniqueConstraint("instrument_id", "benchmark_instrument_id", "purpose"),
        {"schema": "core"},
    )

    benchmark_map_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.instrument.instrument_id"),
        nullable=False,
    )
    benchmark_instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.instrument.instrument_id"),
        nullable=False,
    )
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(
        SmallInteger, server_default="100", nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)

    # relationships
    instrument: Mapped["Instrument"] = relationship(
        "Instrument",
        back_populates="benchmark_maps",
        foreign_keys=[instrument_id],
    )
    benchmark_instrument: Mapped["Instrument"] = relationship(
        "Instrument",
        back_populates="benchmark_of",
        foreign_keys=[benchmark_instrument_id],
    )
