"""Extension registry schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from backend.schemas.common import OrmBase, PaginatedResponse

# --- Feature Flags ---

class FeatureFlagRead(OrmBase):
    """Feature flag response."""
    feature_flag_id: UUID
    flag_code: str
    display_name: str
    description: str | None = None
    owner_team: str | None = None
    rollout_state: str
    default_value: bool
    targeting_rules_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class FeatureFlagCreate(OrmBase):
    """Feature flag creation."""
    flag_code: str
    display_name: str
    description: str | None = None
    owner_team: str | None = None
    rollout_state: str = "disabled"
    default_value: bool = False
    targeting_rules_json: dict[str, Any] = {}


class FeatureFlagUpdate(OrmBase):
    """Feature flag update."""
    display_name: str | None = None
    rollout_state: str | None = None
    default_value: bool | None = None
    targeting_rules_json: dict[str, Any] | None = None


class FeatureFlagList(PaginatedResponse):
    """Paginated feature flags."""
    items: list[FeatureFlagRead]


# --- Schema Registry ---

class SchemaRegistryRead(OrmBase):
    """Schema registry entry response."""
    schema_registry_id: UUID
    schema_name: str
    semantic_version: str
    status: str
    owner_team: str | None = None
    json_schema_uri: str | None = None
    backward_compatible_from: str | None = None
    forward_compatible_to: str | None = None
    rollout_state: str
    created_at: datetime


class SchemaRegistryCreate(OrmBase):
    """Schema registry entry creation."""
    schema_name: str
    semantic_version: str
    status: str = "draft"
    owner_team: str | None = None
    json_schema_uri: str | None = None
    backward_compatible_from: str | None = None
    forward_compatible_to: str | None = None
    rollout_state: str = "internal"


class SchemaRegistryList(PaginatedResponse):
    """Paginated schema registry entries."""
    items: list[SchemaRegistryRead]


# --- Plugin Registry ---

class PluginRegistryRead(OrmBase):
    """Plugin registry response."""
    plugin_registry_id: UUID
    plugin_code: str
    plugin_type: str
    display_name: str
    plugin_version: str
    plugin_api_version: str
    status: str
    owner_team: str | None = None
    capabilities_json: list[Any]
    required_permissions_json: list[Any]
    supported_markets_json: list[Any]
    manifest_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PluginRegistryCreate(OrmBase):
    """Plugin registry creation."""
    plugin_code: str
    plugin_type: str
    display_name: str
    plugin_version: str
    plugin_api_version: str
    capabilities_json: list[Any] = []
    required_permissions_json: list[Any] = []
    supported_markets_json: list[Any] = []
    manifest_json: dict[str, Any] = {}


class PluginRegistryList(PaginatedResponse):
    """Paginated plugin registry."""
    items: list[PluginRegistryRead]


# --- Event Type Registry ---

class EventTypeRegistryRead(OrmBase):
    """Event type registry response."""
    event_type_registry_id: UUID
    event_type_code: str
    display_name: str
    event_family: str
    status: str
    default_directionality: str | None = None
    metadata_json: dict[str, Any]


class EventTypeRegistryCreate(OrmBase):
    """Event type registry creation."""
    event_type_code: str
    display_name: str
    event_family: str
    status: str = "provisional"
    default_directionality: str | None = None
    metadata_json: dict[str, Any] = {}


# --- Contract Compatibility ---

class ContractCompatibilityRead(OrmBase):
    """Contract compatibility response."""
    contract_compatibility_id: UUID
    producer_component: str
    consumer_component: str
    schema_name: str
    min_supported_version: str
    max_tested_version: str | None = None
    status: str
    notes: str | None = None
    created_at: datetime


class ContractCompatibilityCreate(OrmBase):
    """Contract compatibility creation."""
    producer_component: str
    consumer_component: str
    schema_name: str
    min_supported_version: str
    max_tested_version: str | None = None
    status: str = "supported"
    notes: str | None = None
