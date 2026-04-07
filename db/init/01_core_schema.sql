
-- Event Intelligence OS v2 (extensible edition)
-- PostgreSQL 16+ recommended
-- Core DDL for detailed design pack (base schema)
-- Note: keep append-oriented ledgers immutable at application level.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS sources;
CREATE SCHEMA IF NOT EXISTS content;
CREATE SCHEMA IF NOT EXISTS forecasting;
CREATE SCHEMA IF NOT EXISTS execution;
CREATE SCHEMA IF NOT EXISTS feedback;
CREATE SCHEMA IF NOT EXISTS ops;

-- =========================================================
-- Core reference data
-- =========================================================

CREATE TABLE IF NOT EXISTS core.app_user (
    user_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text NOT NULL UNIQUE,
    display_name text NOT NULL,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','disabled','invited')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.role (
    role_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    role_code text NOT NULL UNIQUE,
    display_name text NOT NULL
);

CREATE TABLE IF NOT EXISTS core.user_role (
    user_id uuid NOT NULL REFERENCES core.app_user(user_id),
    role_id uuid NOT NULL REFERENCES core.role(role_id),
    granted_at timestamptz NOT NULL DEFAULT now(),
    granted_by uuid NULL REFERENCES core.app_user(user_id),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS core.market_profile (
    market_profile_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    market_code text NOT NULL UNIQUE,
    display_name text NOT NULL,
    asset_class text NOT NULL,
    primary_timezone text NOT NULL,
    quote_currency text NOT NULL,
    calendar_code text NOT NULL,
    session_template_json jsonb NOT NULL,
    default_horizons_json jsonb NOT NULL DEFAULT '["1d","5d","20d"]'::jsonb,
    default_risk_rules_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    default_language_priority_json jsonb NOT NULL DEFAULT '["en"]'::jsonb,
    default_source_bundle_id uuid NULL,
    enabled_execution_modes_json jsonb NOT NULL DEFAULT '["replay","shadow","paper","micro_live"]'::jsonb,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.trading_venue (
    venue_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    market_profile_id uuid NOT NULL REFERENCES core.market_profile(market_profile_id),
    venue_code text NOT NULL,
    display_name text NOT NULL,
    country_code text NULL,
    active boolean NOT NULL DEFAULT true,
    UNIQUE (market_profile_id, venue_code)
);

CREATE TABLE IF NOT EXISTS core.instrument (
    instrument_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    market_profile_id uuid NOT NULL REFERENCES core.market_profile(market_profile_id),
    venue_id uuid NULL REFERENCES core.trading_venue(venue_id),
    symbol text NOT NULL,
    display_name text NOT NULL,
    instrument_type text NOT NULL CHECK (instrument_type IN ('equity','etf','index','future','fx','crypto','macro_series','commodity')),
    quote_currency text NOT NULL,
    sector text NULL,
    industry text NULL,
    isin text NULL,
    cusip text NULL,
    figi text NULL,
    lot_size numeric(18,6) NOT NULL DEFAULT 1,
    active boolean NOT NULL DEFAULT true,
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (market_profile_id, symbol)
);

CREATE TABLE IF NOT EXISTS core.instrument_alias (
    alias_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    instrument_id uuid NOT NULL REFERENCES core.instrument(instrument_id),
    alias_type text NOT NULL CHECK (alias_type IN ('ticker','name','cusip','isin','figi','vendor_symbol','regex')),
    alias_value text NOT NULL,
    active boolean NOT NULL DEFAULT true,
    UNIQUE (instrument_id, alias_type, alias_value)
);

CREATE TABLE IF NOT EXISTS core.benchmark_map (
    benchmark_map_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    instrument_id uuid NOT NULL REFERENCES core.instrument(instrument_id),
    benchmark_instrument_id uuid NOT NULL REFERENCES core.instrument(instrument_id),
    purpose text NOT NULL CHECK (purpose IN ('sector_relative','market_relative','country_relative','vol_proxy')),
    priority smallint NOT NULL DEFAULT 100,
    active boolean NOT NULL DEFAULT true,
    UNIQUE (instrument_id, benchmark_instrument_id, purpose)
);

-- =========================================================
-- Source registry / universe / watch planning
-- =========================================================

CREATE TABLE IF NOT EXISTS sources.source_registry (
    source_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_code text NOT NULL UNIQUE,
    display_name text NOT NULL,
    source_type text NOT NULL CHECK (source_type IN ('official','vendor','exchange','regulator','macro_calendar','community','internal')),
    adapter_type text NOT NULL CHECK (adapter_type IN ('rss','json_api','html_scrape','websocket','calendar','file_drop','manual_entry')),
    trust_tier text NOT NULL CHECK (trust_tier IN ('official','high_vendor','medium_vendor','low_vendor','experimental')),
    latency_class text NOT NULL CHECK (latency_class IN ('realtime','scheduled','delayed','batch')),
    auth_requirements_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    coverage_tags_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    markets_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    languages_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    retention_days integer NOT NULL DEFAULT 365,
    legal_notes text NULL,
    owner_team text NULL,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','disabled','retired')),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sources.source_endpoint (
    source_endpoint_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id uuid NOT NULL REFERENCES sources.source_registry(source_id),
    endpoint_name text NOT NULL,
    endpoint_url text NOT NULL,
    endpoint_type text NOT NULL CHECK (endpoint_type IN ('rss','json_api','html','websocket','calendar','file')),
    auth_profile text NULL,
    polling_interval_sec integer NULL,
    rate_limit_per_minute integer NULL,
    active boolean NOT NULL DEFAULT true,
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (source_id, endpoint_name)
);

CREATE TABLE IF NOT EXISTS sources.source_bundle (
    source_bundle_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bundle_code text NOT NULL UNIQUE,
    display_name text NOT NULL,
    market_profile_id uuid NULL REFERENCES core.market_profile(market_profile_id),
    bundle_scope text NOT NULL CHECK (bundle_scope IN ('market_core','sector_overlay','event_overlay','temporary')),
    applies_to_asset_class text NULL,
    applies_to_sector text NULL,
    active boolean NOT NULL DEFAULT true,
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

ALTER TABLE core.market_profile
    ADD CONSTRAINT fk_market_profile_default_source_bundle
    FOREIGN KEY (default_source_bundle_id) REFERENCES sources.source_bundle(source_bundle_id);

CREATE TABLE IF NOT EXISTS sources.source_bundle_item (
    source_bundle_item_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_bundle_id uuid NOT NULL REFERENCES sources.source_bundle(source_bundle_id),
    source_id uuid NOT NULL REFERENCES sources.source_registry(source_id),
    priority smallint NOT NULL DEFAULT 100,
    activation_rule_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    ttl_hours integer NULL,
    required boolean NOT NULL DEFAULT false,
    UNIQUE (source_bundle_id, source_id)
);

CREATE TABLE IF NOT EXISTS sources.source_candidate (
    source_candidate_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    proposed_source_code text NOT NULL,
    display_name text NOT NULL,
    proposed_adapter_type text NOT NULL,
    proposal_type text NOT NULL CHECK (proposal_type IN ('new_source_candidate','bundle_change','endpoint_change')),
    why_now text NOT NULL,
    expected_coverage_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    linked_market_profile_id uuid NULL REFERENCES core.market_profile(market_profile_id),
    linked_bundle_id uuid NULL REFERENCES sources.source_bundle(source_bundle_id),
    proposed_by_type text NOT NULL CHECK (proposed_by_type IN ('llm','user','system')),
    proposed_by text NOT NULL,
    status text NOT NULL DEFAULT 'candidate' CHECK (status IN ('candidate','provisional','validated','production','retired','rejected')),
    review_notes text NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    reviewed_at timestamptz NULL
);

CREATE TABLE IF NOT EXISTS sources.universe_set (
    universe_set_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    universe_code text NOT NULL UNIQUE,
    market_profile_id uuid NOT NULL REFERENCES core.market_profile(market_profile_id),
    description text NULL,
    selection_rule_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sources.universe_member (
    universe_set_id uuid NOT NULL REFERENCES sources.universe_set(universe_set_id),
    instrument_id uuid NOT NULL REFERENCES core.instrument(instrument_id),
    weight_hint numeric(18,8) NULL,
    tags_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    added_at timestamptz NOT NULL DEFAULT now(),
    removed_at timestamptz NULL,
    PRIMARY KEY (universe_set_id, instrument_id)
);

CREATE TABLE IF NOT EXISTS sources.watch_plan (
    watch_plan_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    market_profile_id uuid NOT NULL REFERENCES core.market_profile(market_profile_id),
    universe_set_id uuid NULL REFERENCES sources.universe_set(universe_set_id),
    execution_mode text NOT NULL CHECK (execution_mode IN ('replay','shadow','paper','micro_live','live')),
    plan_reason_codes_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    portfolio_tags_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    generated_at timestamptz NOT NULL DEFAULT now(),
    generated_by text NOT NULL DEFAULT 'system',
    active boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS sources.watch_plan_item (
    watch_plan_item_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    watch_plan_id uuid NOT NULL REFERENCES sources.watch_plan(watch_plan_id),
    source_id uuid NOT NULL REFERENCES sources.source_registry(source_id),
    source_bundle_id uuid NULL REFERENCES sources.source_bundle(source_bundle_id),
    priority smallint NOT NULL DEFAULT 100,
    is_temporary boolean NOT NULL DEFAULT false,
    ttl_hours integer NULL,
    state text NOT NULL DEFAULT 'planned' CHECK (state IN ('planned','running','paused','failed','completed')),
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (watch_plan_id, source_id)
);

CREATE TABLE IF NOT EXISTS ops.watcher_instance (
    watcher_instance_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id uuid NOT NULL REFERENCES sources.source_registry(source_id),
    watch_plan_item_id uuid NULL REFERENCES sources.watch_plan_item(watch_plan_item_id),
    execution_mode text NOT NULL CHECK (execution_mode IN ('replay','shadow','paper','micro_live','live')),
    started_at timestamptz NOT NULL DEFAULT now(),
    last_heartbeat_at timestamptz NULL,
    status text NOT NULL DEFAULT 'running' CHECK (status IN ('running','stopped','degraded','failed')),
    error_count integer NOT NULL DEFAULT 0,
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

-- =========================================================
-- Content / event ingestion
-- =========================================================

CREATE TABLE IF NOT EXISTS content.dedup_cluster (
    dedup_cluster_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dedup_key text NOT NULL UNIQUE,
    representative_doc_id uuid NULL,
    cluster_size integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS content.raw_document (
    raw_document_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id uuid NOT NULL REFERENCES sources.source_registry(source_id),
    dedup_cluster_id uuid NULL REFERENCES content.dedup_cluster(dedup_cluster_id),
    native_doc_id text NULL,
    headline text NULL,
    url text NULL,
    language_code text NULL,
    source_tier text NOT NULL,
    published_at timestamptz NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now(),
    effective_at timestamptz NULL,
    content_hash text NOT NULL,
    correction_of_doc_id uuid NULL REFERENCES content.raw_document(raw_document_id),
    raw_text text NULL,
    raw_payload_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    visibility_scope text NOT NULL DEFAULT 'internal' CHECK (visibility_scope IN ('internal','restricted','hidden')),
    market_profile_hint_id uuid NULL REFERENCES core.market_profile(market_profile_id),
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (source_id, native_doc_id),
    UNIQUE (source_id, content_hash)
);

ALTER TABLE content.dedup_cluster
    ADD CONSTRAINT fk_dedup_cluster_representative_doc
    FOREIGN KEY (representative_doc_id) REFERENCES content.raw_document(raw_document_id);

CREATE TABLE IF NOT EXISTS content.document_asset_link (
    document_asset_link_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_document_id uuid NOT NULL REFERENCES content.raw_document(raw_document_id),
    instrument_id uuid NOT NULL REFERENCES core.instrument(instrument_id),
    link_type text NOT NULL CHECK (link_type IN ('direct','sector','benchmark','macro','uncertain')),
    confidence numeric(5,4) NOT NULL DEFAULT 0.5,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS content.event_ledger (
    event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_document_id uuid NOT NULL REFERENCES content.raw_document(raw_document_id),
    event_type text NOT NULL,
    issuer_instrument_id uuid NULL REFERENCES core.instrument(instrument_id),
    market_profile_id uuid NULL REFERENCES core.market_profile(market_profile_id),
    event_time timestamptz NULL,
    direction_hint text NULL CHECK (direction_hint IN ('positive','negative','neutral','mixed','unknown')),
    materiality numeric(5,4) NULL,
    novelty numeric(5,4) NULL,
    corroboration_count integer NOT NULL DEFAULT 0,
    extraction_version text NOT NULL,
    schema_version text NOT NULL,
    verification_status text NOT NULL DEFAULT 'extracted' CHECK (verification_status IN ('extracted','verified','invalid','superseded','archived')),
    supersedes_event_id uuid NULL REFERENCES content.event_ledger(event_id),
    event_json jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS content.event_asset_impact (
    event_asset_impact_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id uuid NOT NULL REFERENCES content.event_ledger(event_id),
    instrument_id uuid NOT NULL REFERENCES core.instrument(instrument_id),
    impact_role text NOT NULL CHECK (impact_role IN ('issuer','supplier','customer','sector','benchmark','macro_proxy','peer')),
    direction_hint text NULL CHECK (direction_hint IN ('positive','negative','neutral','mixed','unknown')),
    confidence numeric(5,4) NOT NULL DEFAULT 0.5,
    UNIQUE (event_id, instrument_id, impact_role)
);

CREATE TABLE IF NOT EXISTS content.event_evidence_link (
    event_evidence_link_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id uuid NOT NULL REFERENCES content.event_ledger(event_id),
    raw_document_id uuid NOT NULL REFERENCES content.raw_document(raw_document_id),
    evidence_kind text NOT NULL CHECK (evidence_kind IN ('official','headline','commentary','calendar','market_snapshot','manual_note')),
    span_start integer NULL,
    span_end integer NULL,
    weight numeric(5,4) NOT NULL DEFAULT 1.0,
    UNIQUE (event_id, raw_document_id, evidence_kind, span_start, span_end)
);

-- =========================================================
-- Retrieval / reasoning / forecasting / decisions
-- =========================================================

CREATE TABLE IF NOT EXISTS forecasting.retrieval_set (
    retrieval_set_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id uuid NULL REFERENCES content.event_ledger(event_id),
    retrieval_version text NOT NULL,
    retrieval_mode text NOT NULL CHECK (retrieval_mode IN ('episodic','semantic','mixed','manual')),
    created_at timestamptz NOT NULL DEFAULT now(),
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS forecasting.retrieval_item (
    retrieval_item_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    retrieval_set_id uuid NOT NULL REFERENCES forecasting.retrieval_set(retrieval_set_id),
    item_type text NOT NULL CHECK (item_type IN ('raw_document','event','semantic_stat','case','market_snapshot')),
    item_ref_id uuid NULL,
    item_ref_text text NULL,
    rank smallint NOT NULL DEFAULT 1,
    similarity_score numeric(8,6) NULL,
    selected_by text NOT NULL DEFAULT 'rule',
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS forecasting.reasoning_trace (
    reasoning_trace_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id uuid NULL REFERENCES content.event_ledger(event_id),
    retrieval_set_id uuid NULL REFERENCES forecasting.retrieval_set(retrieval_set_id),
    trace_version text NOT NULL,
    trace_json jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS forecasting.forecast_ledger (
    forecast_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id uuid NULL REFERENCES content.event_ledger(event_id),
    instrument_id uuid NOT NULL REFERENCES core.instrument(instrument_id),
    benchmark_instrument_id uuid NULL REFERENCES core.instrument(instrument_id),
    market_profile_id uuid NOT NULL REFERENCES core.market_profile(market_profile_id),
    reasoning_trace_id uuid NULL REFERENCES forecasting.reasoning_trace(reasoning_trace_id),
    model_family text NOT NULL,
    model_version text NOT NULL,
    worker_id text NOT NULL,
    prompt_template_id text NOT NULL,
    prompt_version text NOT NULL,
    forecast_mode text NOT NULL CHECK (forecast_mode IN ('replay','shadow','paper','micro_live','live')),
    forecasted_at timestamptz NOT NULL DEFAULT now(),
    confidence numeric(5,4) NULL,
    no_trade_reason_codes_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    forecast_json jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS forecasting.forecast_horizon (
    forecast_horizon_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    forecast_id uuid NOT NULL REFERENCES forecasting.forecast_ledger(forecast_id),
    horizon_code text NOT NULL CHECK (horizon_code IN ('1d','5d','20d','1w','1m')),
    p_outperform_benchmark numeric(5,4) NULL,
    p_underperform_benchmark numeric(5,4) NULL,
    p_downside_barrier numeric(5,4) NULL,
    ret_q10 numeric(18,8) NULL,
    ret_q50 numeric(18,8) NULL,
    ret_q90 numeric(18,8) NULL,
    vol_forecast numeric(18,8) NULL,
    UNIQUE (forecast_id, horizon_code)
);

CREATE TABLE IF NOT EXISTS forecasting.decision_ledger (
    decision_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    forecast_id uuid NOT NULL REFERENCES forecasting.forecast_ledger(forecast_id),
    market_profile_id uuid NOT NULL REFERENCES core.market_profile(market_profile_id),
    execution_mode text NOT NULL CHECK (execution_mode IN ('replay','shadow','paper','micro_live','live')),
    score numeric(8,6) NOT NULL,
    action text NOT NULL CHECK (action IN ('long_candidate','short_candidate','no_trade','wait_manual','reduce','exit')),
    decision_status text NOT NULL CHECK (decision_status IN ('candidate','waiting_manual','approved','rejected','submitted_to_execution','suppressed','canceled')),
    policy_version text NOT NULL,
    size_cap numeric(18,8) NULL,
    waiting_on_prompt_task_id uuid NULL,
    reason_codes_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    decided_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS forecasting.decision_reason (
    decision_reason_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id uuid NOT NULL REFERENCES forecasting.decision_ledger(decision_id),
    source_of_reason text NOT NULL CHECK (source_of_reason IN ('agent','baseline','manual_bridge','risk','policy')),
    reason_code text NOT NULL,
    score_contribution numeric(10,6) NULL,
    message text NULL
);

CREATE TABLE IF NOT EXISTS forecasting.prompt_task (
    prompt_task_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id uuid NOT NULL REFERENCES forecasting.decision_ledger(decision_id),
    task_type text NOT NULL CHECK (task_type IN ('pretrade_review','novel_event_review','source_review','postmortem_review')),
    prompt_template_id text NOT NULL,
    prompt_version text NOT NULL,
    prompt_text text NOT NULL,
    prompt_schema_name text NOT NULL,
    prompt_schema_version text NOT NULL,
    evidence_bundle_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    deadline_at timestamptz NOT NULL,
    status text NOT NULL CHECK (status IN ('created','visible','submitted','parsed','needs_reformat','accepted','rejected','expired','canceled')),
    created_by uuid NULL REFERENCES core.app_user(user_id),
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE forecasting.decision_ledger
    ADD CONSTRAINT fk_decision_waiting_prompt_task
    FOREIGN KEY (waiting_on_prompt_task_id) REFERENCES forecasting.prompt_task(prompt_task_id);

CREATE TABLE IF NOT EXISTS forecasting.prompt_response (
    prompt_response_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_task_id uuid NOT NULL REFERENCES forecasting.prompt_task(prompt_task_id),
    submitted_by uuid NULL REFERENCES core.app_user(user_id),
    model_name_user_entered text NOT NULL,
    submitted_at timestamptz NOT NULL DEFAULT now(),
    raw_response text NOT NULL,
    parsed_json jsonb NULL,
    schema_valid boolean NOT NULL DEFAULT false,
    accepted_for_scoring boolean NOT NULL DEFAULT false,
    final_weight numeric(5,4) NULL,
    parser_version text NULL,
    UNIQUE (prompt_task_id, submitted_at)
);

-- =========================================================
-- Execution / positions
-- =========================================================

CREATE TABLE IF NOT EXISTS execution.order_ledger (
    order_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id uuid NOT NULL REFERENCES forecasting.decision_ledger(decision_id),
    instrument_id uuid NOT NULL REFERENCES core.instrument(instrument_id),
    execution_mode text NOT NULL CHECK (execution_mode IN ('replay','shadow','paper','micro_live','live')),
    broker_name text NOT NULL,
    client_order_id text NOT NULL UNIQUE,
    broker_order_id text NULL,
    side text NOT NULL CHECK (side IN ('buy','sell')),
    order_type text NOT NULL CHECK (order_type IN ('market','limit','stop','stop_limit')),
    time_in_force text NOT NULL,
    session_type text NOT NULL CHECK (session_type IN ('premarket','regular','postmarket','overnight')),
    qty numeric(18,8) NOT NULL,
    limit_price numeric(18,8) NULL,
    stop_price numeric(18,8) NULL,
    status text NOT NULL CHECK (status IN ('new','accepted','partially_filled','filled','canceled','rejected','expired')),
    status_reason text NULL,
    submitted_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS execution.execution_fill (
    fill_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id uuid NOT NULL REFERENCES execution.order_ledger(order_id),
    fill_time timestamptz NOT NULL,
    fill_price numeric(18,8) NOT NULL,
    fill_qty numeric(18,8) NOT NULL,
    fee_estimate numeric(18,8) NULL,
    liquidity_flag text NULL,
    fill_source text NOT NULL CHECK (fill_source IN ('replay','paper','live','adjusted_overlay')),
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS execution.position_snapshot (
    position_snapshot_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    as_of timestamptz NOT NULL,
    execution_mode text NOT NULL CHECK (execution_mode IN ('replay','shadow','paper','micro_live','live')),
    instrument_id uuid NOT NULL REFERENCES core.instrument(instrument_id),
    position_qty numeric(18,8) NOT NULL DEFAULT 0,
    average_cost numeric(18,8) NULL,
    mark_price numeric(18,8) NULL,
    unrealized_pnl numeric(18,8) NULL,
    realized_pnl numeric(18,8) NULL,
    snapshot_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

-- =========================================================
-- Feedback / reliability
-- =========================================================

CREATE TABLE IF NOT EXISTS feedback.outcome_ledger (
    outcome_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    forecast_id uuid NOT NULL REFERENCES forecasting.forecast_ledger(forecast_id),
    horizon_code text NOT NULL CHECK (horizon_code IN ('1d','5d','20d','1w','1m')),
    computed_at timestamptz NOT NULL DEFAULT now(),
    horizon_end_at timestamptz NULL,
    realized_abs_return numeric(18,8) NULL,
    realized_rel_return numeric(18,8) NULL,
    benchmark_return numeric(18,8) NULL,
    barrier_hit boolean NULL,
    mae numeric(18,8) NULL,
    mfe numeric(18,8) NULL,
    outcome_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (forecast_id, horizon_code)
);

CREATE TABLE IF NOT EXISTS feedback.postmortem_ledger (
    postmortem_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    forecast_id uuid NOT NULL REFERENCES forecasting.forecast_ledger(forecast_id),
    outcome_id uuid NULL REFERENCES feedback.outcome_ledger(outcome_id),
    verdict text NOT NULL CHECK (verdict IN ('correct','wrong','mixed','insufficient')),
    failure_codes_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    requires_source_review boolean NOT NULL DEFAULT false,
    requires_prompt_review boolean NOT NULL DEFAULT false,
    judge_version text NOT NULL,
    postmortem_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (forecast_id)
);

CREATE TABLE IF NOT EXISTS feedback.reliability_stat (
    reliability_stat_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dimension_hash text NOT NULL UNIQUE,
    market_profile_id uuid NULL REFERENCES core.market_profile(market_profile_id),
    source_id uuid NULL REFERENCES sources.source_registry(source_id),
    event_type text NULL,
    sector text NULL,
    horizon_code text NULL,
    model_family text NULL,
    manual_model_name text NULL,
    sample_size integer NOT NULL DEFAULT 0,
    hit_rate numeric(8,6) NULL,
    brier numeric(8,6) NULL,
    calibration_error numeric(8,6) NULL,
    avg_rel_return numeric(18,8) NULL,
    avg_mae numeric(18,8) NULL,
    last_validated_at timestamptz NULL,
    stats_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS feedback.manual_model_reliability (
    manual_model_reliability_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name text NOT NULL,
    market_profile_id uuid NULL REFERENCES core.market_profile(market_profile_id),
    event_type text NULL,
    horizon_code text NULL,
    sample_size integer NOT NULL DEFAULT 0,
    schema_valid_rate numeric(8,6) NULL,
    accepted_rate numeric(8,6) NULL,
    hit_rate numeric(8,6) NULL,
    brier numeric(8,6) NULL,
    calibration_error numeric(8,6) NULL,
    avg_rel_return numeric(18,8) NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (model_name, market_profile_id, event_type, horizon_code)
);

-- =========================================================
-- Ops / audit / config
-- =========================================================

CREATE TABLE IF NOT EXISTS ops.audit_log (
    audit_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_type text NOT NULL CHECK (actor_type IN ('user','system')),
    actor_user_id uuid NULL REFERENCES core.app_user(user_id),
    actor_label text NOT NULL,
    action text NOT NULL,
    target_type text NOT NULL,
    target_id text NOT NULL,
    before_json jsonb NULL,
    after_json jsonb NULL,
    reason text NULL,
    trace_id text NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ops.kill_switch (
    kill_switch_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    scope_type text NOT NULL CHECK (scope_type IN ('global','market','strategy','source','broker')),
    scope_key text NOT NULL,
    active boolean NOT NULL DEFAULT true,
    reason text NOT NULL,
    activated_by uuid NULL REFERENCES core.app_user(user_id),
    activated_at timestamptz NOT NULL DEFAULT now(),
    cleared_at timestamptz NULL,
    UNIQUE (scope_type, scope_key)
);

CREATE TABLE IF NOT EXISTS ops.system_config (
    config_key text PRIMARY KEY,
    config_value_json jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    updated_by uuid NULL REFERENCES core.app_user(user_id)
);

CREATE TABLE IF NOT EXISTS ops.job_run (
    job_run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type text NOT NULL,
    execution_mode text NOT NULL CHECK (execution_mode IN ('replay','shadow','paper','micro_live','live')),
    status text NOT NULL CHECK (status IN ('queued','running','succeeded','failed','canceled')),
    requested_by uuid NULL REFERENCES core.app_user(user_id),
    started_at timestamptz NULL,
    finished_at timestamptz NULL,
    job_args_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    result_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

-- =========================================================
-- Indexes
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_instrument_market_symbol ON core.instrument (market_profile_id, symbol);
CREATE INDEX IF NOT EXISTS idx_source_registry_status ON sources.source_registry (status, trust_tier);
CREATE INDEX IF NOT EXISTS idx_watch_plan_market_generated ON sources.watch_plan (market_profile_id, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_watcher_instance_status ON ops.watcher_instance (status, last_heartbeat_at DESC);
CREATE INDEX IF NOT EXISTS idx_raw_document_source_published ON content.raw_document (source_id, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_raw_document_published ON content.raw_document (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_doc_asset_link_instrument ON content.document_asset_link (instrument_id, raw_document_id);
CREATE INDEX IF NOT EXISTS idx_event_ledger_event_time ON content.event_ledger (event_time DESC);
CREATE INDEX IF NOT EXISTS idx_event_ledger_event_type ON content.event_ledger (event_type, event_time DESC);
CREATE INDEX IF NOT EXISTS idx_event_asset_impact_instrument ON content.event_asset_impact (instrument_id, event_id);
CREATE INDEX IF NOT EXISTS idx_forecast_ledger_instrument ON forecasting.forecast_ledger (instrument_id, forecasted_at DESC);
CREATE INDEX IF NOT EXISTS idx_forecast_horizon_lookup ON forecasting.forecast_horizon (horizon_code, p_outperform_benchmark DESC);
CREATE INDEX IF NOT EXISTS idx_decision_status_time ON forecasting.decision_ledger (decision_status, decided_at DESC);
CREATE INDEX IF NOT EXISTS idx_prompt_task_status_deadline ON forecasting.prompt_task (status, deadline_at);
CREATE INDEX IF NOT EXISTS idx_prompt_response_task ON forecasting.prompt_response (prompt_task_id, submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_order_ledger_status_time ON execution.order_ledger (status, submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_execution_fill_order ON execution.execution_fill (order_id, fill_time);
CREATE INDEX IF NOT EXISTS idx_position_snapshot_asof ON execution.position_snapshot (execution_mode, as_of DESC);
CREATE INDEX IF NOT EXISTS idx_outcome_forecast_horizon ON feedback.outcome_ledger (forecast_id, horizon_code);
CREATE INDEX IF NOT EXISTS idx_postmortem_verdict ON feedback.postmortem_ledger (verdict, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON ops.audit_log (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_kill_switch_active ON ops.kill_switch (active, scope_type);

-- =========================================================
-- Representative views
-- =========================================================

CREATE OR REPLACE VIEW forecasting.vw_latest_forecast AS
SELECT DISTINCT ON (fl.instrument_id)
    fl.instrument_id,
    fl.forecast_id,
    fl.market_profile_id,
    fl.model_family,
    fl.model_version,
    fl.prompt_version,
    fl.forecasted_at,
    fl.confidence,
    fl.forecast_json
FROM forecasting.forecast_ledger fl
ORDER BY fl.instrument_id, fl.forecasted_at DESC;

CREATE OR REPLACE VIEW forecasting.vw_prompt_task_queue AS
SELECT
    pt.prompt_task_id,
    pt.decision_id,
    pt.task_type,
    pt.status,
    pt.deadline_at,
    d.action,
    d.score,
    f.instrument_id
FROM forecasting.prompt_task pt
JOIN forecasting.decision_ledger d ON d.decision_id = pt.decision_id
JOIN forecasting.forecast_ledger f ON f.forecast_id = d.forecast_id
WHERE pt.status IN ('created','visible','submitted','needs_reformat','expired');

CREATE OR REPLACE VIEW feedback.vw_source_gap_summary AS
SELECT
    fl.market_profile_id,
    ce.event_type,
    jsonb_array_elements_text(pm.failure_codes_json) AS failure_code,
    count(*) AS occurrences
FROM feedback.postmortem_ledger pm
JOIN forecasting.forecast_ledger fl ON fl.forecast_id = pm.forecast_id
LEFT JOIN content.event_ledger ce ON ce.event_id = fl.event_id
GROUP BY fl.market_profile_id, ce.event_type, jsonb_array_elements_text(pm.failure_codes_json);

CREATE OR REPLACE VIEW execution.vw_order_with_latest_fill AS
SELECT
    o.order_id,
    o.client_order_id,
    o.execution_mode,
    o.status,
    o.instrument_id,
    o.side,
    o.qty,
    o.limit_price,
    o.submitted_at,
    max(f.fill_time) AS latest_fill_time,
    sum(f.fill_qty) AS filled_qty
FROM execution.order_ledger o
LEFT JOIN execution.execution_fill f ON f.order_id = o.order_id
GROUP BY o.order_id;
