"""Tests for extension registry Pydantic schemas."""

from datetime import UTC, datetime
from uuid import uuid4

from backend.schemas.extensions import (
    ContractCompatibilityCreate,
    ContractCompatibilityRead,
    EventTypeRegistryCreate,
    EventTypeRegistryRead,
    FeatureFlagCreate,
    FeatureFlagRead,
    FeatureFlagUpdate,
    PluginRegistryCreate,
    PluginRegistryRead,
    SchemaRegistryCreate,
    SchemaRegistryRead,
)


def test_feature_flag_create_defaults():
    """FeatureFlagCreate should have correct defaults."""
    ff = FeatureFlagCreate(
        flag_code="enable_live_trading",
        display_name="Enable Live Trading",
    )
    assert ff.rollout_state == "disabled"
    assert ff.default_value is False
    assert ff.targeting_rules_json == {}


def test_feature_flag_update_partial():
    """FeatureFlagUpdate should allow partial updates."""
    update = FeatureFlagUpdate(rollout_state="internal")
    dumped = update.model_dump(exclude_unset=True)
    assert dumped == {"rollout_state": "internal"}
    assert "default_value" not in dumped


def test_feature_flag_read():
    """FeatureFlagRead should parse correctly."""
    now = datetime.now(tz=UTC)
    ff = FeatureFlagRead(
        feature_flag_id=uuid4(),
        flag_code="test_flag",
        display_name="Test Flag",
        rollout_state="disabled",
        default_value=False,
        targeting_rules_json={},
        created_at=now,
        updated_at=now,
    )
    assert ff.flag_code == "test_flag"


def test_schema_registry_create_defaults():
    """SchemaRegistryCreate should have correct defaults."""
    sr = SchemaRegistryCreate(
        schema_name="forecast",
        semantic_version="1.0.0",
    )
    assert sr.status == "draft"
    assert sr.rollout_state == "internal"


def test_schema_registry_read():
    """SchemaRegistryRead should parse correctly."""
    sr = SchemaRegistryRead(
        schema_registry_id=uuid4(),
        schema_name="event_record",
        semantic_version="1.2.0",
        status="active",
        rollout_state="live",
        created_at=datetime.now(tz=UTC),
    )
    assert sr.semantic_version == "1.2.0"


def test_plugin_registry_create_defaults():
    """PluginRegistryCreate should have correct defaults."""
    pr = PluginRegistryCreate(
        plugin_code="forecast-overlay",
        plugin_type="panel",
        display_name="Forecast Overlay Panel",
        plugin_version="1.0.0",
        plugin_api_version="1.0.0",
    )
    assert pr.capabilities_json == []
    assert pr.manifest_json == {}


def test_plugin_registry_read():
    """PluginRegistryRead should parse correctly."""
    now = datetime.now(tz=UTC)
    pr = PluginRegistryRead(
        plugin_registry_id=uuid4(),
        plugin_code="test-plugin",
        plugin_type="app_page",
        display_name="Test Plugin",
        plugin_version="1.0.0",
        plugin_api_version="1.0.0",
        status="disabled",
        capabilities_json=["read_events"],
        required_permissions_json=["viewer"],
        supported_markets_json=["US_EQUITY"],
        manifest_json={"entry": "index.js"},
        created_at=now,
        updated_at=now,
    )
    assert pr.status == "disabled"
    assert "read_events" in pr.capabilities_json


def test_event_type_registry_create_defaults():
    """EventTypeRegistryCreate should default to provisional."""
    et = EventTypeRegistryCreate(
        event_type_code="earnings_surprise",
        display_name="Earnings Surprise",
        event_family="corporate",
    )
    assert et.status == "provisional"
    assert et.metadata_json == {}


def test_event_type_registry_read():
    """EventTypeRegistryRead should parse correctly."""
    et = EventTypeRegistryRead(
        event_type_registry_id=uuid4(),
        event_type_code="macro_release",
        display_name="Macro Release",
        event_family="macro",
        status="active",
        default_directionality="mixed",
        metadata_json={},
    )
    assert et.event_family == "macro"


def test_contract_compatibility_create_defaults():
    """ContractCompatibilityCreate defaults to supported."""
    cc = ContractCompatibilityCreate(
        producer_component="forecast_worker",
        consumer_component="decision_engine",
        schema_name="forecast",
        min_supported_version="1.0.0",
    )
    assert cc.status == "supported"


def test_contract_compatibility_read():
    """ContractCompatibilityRead should parse correctly."""
    cc = ContractCompatibilityRead(
        contract_compatibility_id=uuid4(),
        producer_component="ingest",
        consumer_component="extractor",
        schema_name="event_record",
        min_supported_version="1.0.0",
        max_tested_version="1.2.0",
        status="supported",
        created_at=datetime.now(tz=UTC),
    )
    assert cc.max_tested_version == "1.2.0"
