-- Event Intelligence OS v2
-- Extension-oriented tables and registries
-- Apply after 01_core_schema.sql

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS core.feature_flag (
    feature_flag_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_code text NOT NULL UNIQUE,
    display_name text NOT NULL,
    description text NULL,
    owner_team text NULL,
    rollout_state text NOT NULL DEFAULT 'disabled'
        CHECK (rollout_state IN ('disabled','internal','paper_only','micro_live','live','deprecated')),
    default_value boolean NOT NULL DEFAULT false,
    targeting_rules_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.schema_registry (
    schema_registry_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    schema_name text NOT NULL,
    semantic_version text NOT NULL,
    status text NOT NULL DEFAULT 'active'
        CHECK (status IN ('draft','active','deprecated','retired')),
    owner_team text NULL,
    json_schema_uri text NULL,
    sample_payload_uri text NULL,
    backward_compatible_from text NULL,
    forward_compatible_to text NULL,
    rollout_state text NOT NULL DEFAULT 'internal'
        CHECK (rollout_state IN ('internal','paper_only','micro_live','live')),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (schema_name, semantic_version)
);

CREATE TABLE IF NOT EXISTS core.event_type_registry (
    event_type_registry_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type_code text NOT NULL UNIQUE,
    display_name text NOT NULL,
    event_family text NOT NULL,
    status text NOT NULL DEFAULT 'active'
        CHECK (status IN ('provisional','active','deprecated','retired')),
    default_directionality text NULL
        CHECK (default_directionality IN ('positive','negative','neutral','mixed','unknown')),
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS core.reason_code_registry (
    reason_code_registry_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    reason_code text NOT NULL UNIQUE,
    reason_family text NOT NULL,
    display_name text NOT NULL,
    description text NULL,
    severity text NOT NULL DEFAULT 'medium'
        CHECK (severity IN ('low','medium','high','critical')),
    active boolean NOT NULL DEFAULT true,
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS core.plugin_registry (
    plugin_registry_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_code text NOT NULL UNIQUE,
    plugin_type text NOT NULL
        CHECK (plugin_type IN ('app_page','panel','overlay','action','backend_adapter')),
    display_name text NOT NULL,
    plugin_version text NOT NULL,
    plugin_api_version text NOT NULL,
    status text NOT NULL DEFAULT 'disabled'
        CHECK (status IN ('disabled','enabled','degraded','retired')),
    owner_team text NULL,
    capabilities_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    required_permissions_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    supported_markets_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    manifest_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.worker_adapter_registry (
    worker_adapter_registry_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    adapter_code text NOT NULL UNIQUE,
    adapter_type text NOT NULL
        CHECK (adapter_type IN ('api','cli','manual_bridge','heuristic')),
    display_name text NOT NULL,
    adapter_version text NOT NULL,
    provider_name text NULL,
    status text NOT NULL DEFAULT 'enabled'
        CHECK (status IN ('enabled','disabled','degraded','retired')),
    capability_tags_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    supported_task_types_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    config_schema_ref text NULL,
    healthcheck_config_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.broker_adapter_registry (
    broker_adapter_registry_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    adapter_code text NOT NULL UNIQUE,
    display_name text NOT NULL,
    adapter_version text NOT NULL,
    broker_family text NOT NULL,
    status text NOT NULL DEFAULT 'enabled'
        CHECK (status IN ('enabled','disabled','degraded','retired')),
    capabilities_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    markets_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    config_schema_ref text NULL,
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS forecasting.policy_pack_registry (
    policy_pack_registry_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_pack_code text NOT NULL,
    policy_pack_version text NOT NULL,
    display_name text NOT NULL,
    status text NOT NULL DEFAULT 'active'
        CHECK (status IN ('draft','active','deprecated','retired')),
    market_profile_id uuid NULL REFERENCES core.market_profile(market_profile_id),
    rule_schema_ref text NULL,
    rules_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (policy_pack_code, policy_pack_version)
);

CREATE TABLE IF NOT EXISTS ops.outbox_event (
    outbox_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    topic text NOT NULL,
    partition_key text NULL,
    event_name text NOT NULL,
    event_version text NOT NULL,
    schema_name text NOT NULL,
    schema_version text NOT NULL,
    payload_json jsonb NOT NULL,
    trace_id text NULL,
    idempotency_key text NULL,
    status text NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','published','failed','dead_letter')),
    attempt_count integer NOT NULL DEFAULT 0,
    next_attempt_at timestamptz NULL,
    published_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ops.contract_compatibility (
    contract_compatibility_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    producer_component text NOT NULL,
    consumer_component text NOT NULL,
    schema_name text NOT NULL,
    min_supported_version text NOT NULL,
    max_tested_version text NULL,
    status text NOT NULL DEFAULT 'supported'
        CHECK (status IN ('supported','warning','blocked')),
    notes text NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (producer_component, consumer_component, schema_name, min_supported_version)
);

CREATE INDEX IF NOT EXISTS idx_outbox_status_next_attempt
    ON ops.outbox_event (status, next_attempt_at, created_at);

CREATE INDEX IF NOT EXISTS idx_plugin_registry_status_type
    ON core.plugin_registry (status, plugin_type);

CREATE INDEX IF NOT EXISTS idx_worker_registry_type_status
    ON core.worker_adapter_registry (adapter_type, status);

CREATE INDEX IF NOT EXISTS idx_policy_pack_market_status
    ON forecasting.policy_pack_registry (market_profile_id, status);

COMMENT ON TABLE core.schema_registry IS 'Registry of JSON payload schemas and rollout states';
COMMENT ON TABLE ops.outbox_event IS 'Transactional outbox for internal async events';
