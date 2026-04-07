"""SQLAlchemy ORM models for extension/registry tables across `core` and `ops` schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


# ---------------------------------------------------------------------------
# 1. FeatureFlag  (core schema)
# ---------------------------------------------------------------------------
class FeatureFlag(Base):
    __tablename__ = "feature_flag"
    __table_args__ = (
        CheckConstraint(
            "rollout_state IN ('disabled','internal','paper_only',"
            "'micro_live','live','deprecated')",
            name="ck_feature_flag_rollout_state",
        ),
        {"schema": "core"},
    )

    feature_flag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    flag_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_team: Mapped[str | None] = mapped_column(Text, nullable=True)
    rollout_state: Mapped[str] = mapped_column(
        Text, server_default=text("'disabled'"), nullable=False
    )
    default_value: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    targeting_rules_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# 2. SchemaRegistryEntry  (core schema)
# ---------------------------------------------------------------------------
class SchemaRegistryEntry(Base):
    __tablename__ = "schema_registry"
    __table_args__ = (
        UniqueConstraint(
            "schema_name", "semantic_version",
            name="uq_schema_registry_name_version",
        ),
        CheckConstraint(
            "status IN ('draft','active','deprecated','retired')",
            name="ck_schema_registry_entry_status",
        ),
        CheckConstraint(
            "rollout_state IN ('internal','paper_only',"
            "'micro_live','live')",
            name="ck_schema_registry_entry_rollout_state",
        ),
        {"schema": "core"},
    )

    schema_registry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    schema_name: Mapped[str] = mapped_column(Text, nullable=False)
    semantic_version: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'active'"), nullable=False
    )
    owner_team: Mapped[str | None] = mapped_column(Text, nullable=True)
    json_schema_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_payload_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    backward_compatible_from: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    forward_compatible_to: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    rollout_state: Mapped[str] = mapped_column(
        Text, server_default=text("'internal'"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ---------------------------------------------------------------------------
# 3. EventTypeRegistry  (core schema)
# ---------------------------------------------------------------------------
class EventTypeRegistry(Base):
    __tablename__ = "event_type_registry"
    __table_args__ = (
        CheckConstraint(
            "status IN ('provisional','active','deprecated','retired')",
            name="ck_event_type_registry_status",
        ),
        {"schema": "core"},
    )

    event_type_registry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    event_type_code: Mapped[str] = mapped_column(
        Text, unique=True, nullable=False
    )
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    event_family: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'provisional'"), nullable=False
    )
    default_directionality: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )


# ---------------------------------------------------------------------------
# 4. ReasonCodeRegistry  (core schema)
# ---------------------------------------------------------------------------
class ReasonCodeRegistry(Base):
    __tablename__ = "reason_code_registry"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('low','medium','high','critical')",
            name="ck_reason_code_registry_severity",
        ),
        {"schema": "core"},
    )

    reason_code_registry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    reason_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    reason_family: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(
        Text, server_default=text("'medium'"), nullable=False
    )
    active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )


# ---------------------------------------------------------------------------
# 5. PluginRegistry  (core schema)
# ---------------------------------------------------------------------------
class PluginRegistry(Base):
    __tablename__ = "plugin_registry"
    __table_args__ = (
        CheckConstraint(
            "plugin_type IN ('app_page','panel','overlay','action','backend_adapter')",
            name="ck_plugin_registry_plugin_type",
        ),
        CheckConstraint(
            "status IN ('disabled','enabled','degraded','retired')",
            name="ck_plugin_registry_status",
        ),
        {"schema": "core"},
    )

    plugin_registry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    plugin_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    plugin_type: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    plugin_version: Mapped[str] = mapped_column(Text, nullable=False)
    plugin_api_version: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'disabled'"), nullable=False
    )
    owner_team: Mapped[str | None] = mapped_column(Text, nullable=True)
    capabilities_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    required_permissions_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    supported_markets_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    manifest_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# 6. WorkerAdapterRegistry  (core schema)
# ---------------------------------------------------------------------------
class WorkerAdapterRegistry(Base):
    __tablename__ = "worker_adapter_registry"
    __table_args__ = (
        CheckConstraint(
            "adapter_type IN ('api','cli','manual_bridge','heuristic')",
            name="ck_worker_adapter_registry_adapter_type",
        ),
        CheckConstraint(
            "status IN ('enabled','disabled','degraded','retired')",
            name="ck_worker_adapter_registry_status",
        ),
        {"schema": "core"},
    )

    worker_adapter_registry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    adapter_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    adapter_type: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    adapter_version: Mapped[str] = mapped_column(Text, nullable=False)
    provider_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'enabled'"), nullable=False
    )
    capability_tags_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    supported_task_types_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    config_schema_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    healthcheck_config_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ---------------------------------------------------------------------------
# 7. BrokerAdapterRegistry  (core schema)
# ---------------------------------------------------------------------------
class BrokerAdapterRegistry(Base):
    __tablename__ = "broker_adapter_registry"
    __table_args__ = (
        CheckConstraint(
            "status IN ('enabled','disabled','degraded','retired')",
            name="ck_broker_adapter_registry_status",
        ),
        {"schema": "core"},
    )

    broker_adapter_registry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    adapter_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    adapter_version: Mapped[str] = mapped_column(Text, nullable=False)
    broker_family: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'enabled'"), nullable=False
    )
    capabilities_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    markets_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    config_schema_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ---------------------------------------------------------------------------
# 8. ContractCompatibility  (ops schema)
# ---------------------------------------------------------------------------
class ContractCompatibility(Base):
    __tablename__ = "contract_compatibility"
    __table_args__ = (
        UniqueConstraint(
            "producer_component", "consumer_component",
            "schema_name", "min_supported_version",
            name="uq_contract_compat_producer_consumer_schema_ver",
        ),
        CheckConstraint(
            "status IN ('supported','warning','blocked')",
            name="ck_contract_compatibility_status",
        ),
        {"schema": "ops"},
    )

    contract_compatibility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    producer_component: Mapped[str] = mapped_column(Text, nullable=False)
    consumer_component: Mapped[str] = mapped_column(Text, nullable=False)
    schema_name: Mapped[str] = mapped_column(Text, nullable=False)
    min_supported_version: Mapped[str] = mapped_column(Text, nullable=False)
    max_tested_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'supported'"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
