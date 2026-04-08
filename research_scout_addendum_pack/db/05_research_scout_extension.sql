-- 05_research_scout_extension.sql
-- Research Scout / Autonomous News Exploration extension
-- Designed to layer onto the existing Event Intelligence OS core schemas.
-- Assumes UUID support and append-first ledger discipline.

CREATE SCHEMA IF NOT EXISTS research_ops;

CREATE TABLE IF NOT EXISTS research_ops.research_case (
    case_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_type TEXT NOT NULL CHECK (case_type IN (
        'symbol_context',
        'sector_context',
        'theme_context',
        'cross_symbol_spillover',
        'universe_discovery',
        'source_gap_investigation',
        'postmortem_followup'
    )),
    market_code TEXT NOT NULL,
    primary_symbol TEXT NULL,
    benchmark_symbol TEXT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN (
        'new','monitoring','enriching','awaiting_human','promotion_pending','resolved','retired'
    )),
    priority SMALLINT NOT NULL DEFAULT 50,
    trigger_reason TEXT NULL,
    current_hypothesis_summary TEXT NULL,
    current_question_summary TEXT NULL,
    trace_id TEXT NULL,
    correlation_id TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_research_case_market_status
ON research_ops.research_case (market_code, status, priority DESC);

CREATE INDEX IF NOT EXISTS idx_research_case_primary_symbol
ON research_ops.research_case (primary_symbol);

CREATE TABLE IF NOT EXISTS research_ops.research_scope (
    scope_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES research_ops.research_case(case_id) ON DELETE CASCADE,
    scope_type TEXT NOT NULL CHECK (scope_type IN (
        'symbol','sector','theme','market_profile','source_bundle','issuer','related_entity'
    )),
    scope_key TEXT NOT NULL,
    scope_role TEXT NOT NULL CHECK (scope_role IN (
        'watched','candidate','peer','supplier','customer','benchmark','macro','theme_anchor'
    )),
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_research_scope_case
ON research_ops.research_scope (case_id);

CREATE INDEX IF NOT EXISTS idx_research_scope_type_key
ON research_ops.research_scope (scope_type, scope_key);

CREATE TABLE IF NOT EXISTS research_ops.research_job (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NULL REFERENCES research_ops.research_case(case_id) ON DELETE SET NULL,
    job_type TEXT NOT NULL CHECK (job_type IN (
        'context_deepen',
        'historical_backfill',
        'candidate_discovery',
        'promotion_review',
        'brief_refresh',
        'source_probe'
    )),
    trigger_type TEXT NOT NULL CHECK (trigger_type IN (
        'schedule','event','inquiry','operator','chat','postmortem'
    )),
    budget_class TEXT NOT NULL CHECK (budget_class IN ('low','medium','high')),
    status TEXT NOT NULL CHECK (status IN (
        'queued','running','completed','failed','canceled','stale'
    )),
    worker_adapter TEXT NULL,
    prompt_version TEXT NULL,
    input_hash TEXT NULL,
    result_summary TEXT NULL,
    trace_id TEXT NULL,
    correlation_id TEXT NULL,
    scheduled_at TIMESTAMPTZ NULL,
    started_at TIMESTAMPTZ NULL,
    finished_at TIMESTAMPTZ NULL,
    next_run_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_research_job_status_created
ON research_ops.research_job (status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_research_job_case
ON research_ops.research_job (case_id, created_at DESC);

CREATE TABLE IF NOT EXISTS research_ops.research_query_plan (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES research_ops.research_job(job_id) ON DELETE CASCADE,
    query_kind TEXT NOT NULL CHECK (query_kind IN (
        'symbol_backfill',
        'event_analog_search',
        'peer_scan',
        'theme_scan',
        'relation_confirmation',
        'counterargument_search',
        'source_probe',
        'candidate_validation'
    )),
    source_filter_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    query_text TEXT NOT NULL,
    time_window_start TIMESTAMPTZ NULL,
    time_window_end TIMESTAMPTZ NULL,
    max_docs INTEGER NOT NULL DEFAULT 20,
    status TEXT NOT NULL CHECK (status IN ('planned','executing','completed','failed','canceled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_research_query_plan_job
ON research_ops.research_query_plan (job_id);

CREATE TABLE IF NOT EXISTS research_ops.research_evidence (
    evidence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES research_ops.research_case(case_id) ON DELETE CASCADE,
    source_doc_id TEXT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN (
        'raw_document','event_record','forecast','decision','order','postmortem','inquiry','external_ref'
    )),
    evidence_role TEXT NOT NULL CHECK (evidence_role IN (
        'primary','supporting','counter','historical','candidate_trigger','macro_context'
    )),
    symbol TEXT NULL,
    event_type TEXT NULL,
    published_at TIMESTAMPTZ NULL,
    relevance_score NUMERIC(5,4) NULL,
    novelty_score NUMERIC(5,4) NULL,
    reliability_score NUMERIC(5,4) NULL,
    summary TEXT NULL,
    quote_spans_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_research_evidence_case
ON research_ops.research_evidence (case_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_research_evidence_symbol
ON research_ops.research_evidence (symbol, published_at DESC);

CREATE TABLE IF NOT EXISTS research_ops.research_brief (
    brief_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES research_ops.research_case(case_id) ON DELETE CASCADE,
    brief_kind TEXT NOT NULL CHECK (brief_kind IN (
        'symbol_context',
        'sector_context',
        'theme_context',
        'candidate_snapshot',
        'promotion_memo',
        'historical_context'
    )),
    version INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL CHECK (status IN ('draft','active','superseded','archived')),
    brief_json JSONB NOT NULL,
    expires_at TIMESTAMPTZ NULL,
    trace_id TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_research_brief_case_status
ON research_ops.research_brief (case_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS research_ops.symbol_dossier_snapshot (
    snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_code TEXT NOT NULL,
    symbol TEXT NOT NULL,
    asof TIMESTAMPTZ NOT NULL,
    watch_status TEXT NOT NULL CHECK (watch_status IN (
        'watched','candidate','promoted','retired','archived'
    )),
    benchmark_symbol TEXT NULL,
    current_thesis TEXT NULL,
    payload_json JSONB NOT NULL,
    quality_score NUMERIC(5,4) NULL,
    coverage_score NUMERIC(5,4) NULL,
    research_depth_score NUMERIC(5,4) NULL,
    freshness_class TEXT NOT NULL CHECK (freshness_class IN ('fresh','warm','stale','archived')),
    source_case_id UUID NULL REFERENCES research_ops.research_case(case_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_symbol_dossier_symbol_asof
ON research_ops.symbol_dossier_snapshot (market_code, symbol, asof DESC);

CREATE TABLE IF NOT EXISTS research_ops.candidate_symbol (
    candidate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_code TEXT NOT NULL,
    symbol TEXT NOT NULL,
    discovered_from_case_id UUID NULL REFERENCES research_ops.research_case(case_id) ON DELETE SET NULL,
    discovered_from_event_ref TEXT NULL,
    relation_to_watchlist TEXT NOT NULL CHECK (relation_to_watchlist IN (
        'supplier','customer','competitor','peer','index_peer','macro_sensitive','event_only','unknown'
    )),
    candidate_reason_codes JSONB NOT NULL DEFAULT '[]'::jsonb,
    discovery_score NUMERIC(5,4) NOT NULL DEFAULT 0.0000,
    promotion_score NUMERIC(5,4) NULL,
    status TEXT NOT NULL CHECK (status IN (
        'new','monitoring','needs_more_evidence','promotion_pending','promoted','rejected','expired'
    )),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    promoted_at TIMESTAMPTZ NULL,
    rejected_at TIMESTAMPTZ NULL,
    decision_note TEXT NULL,
    trace_id TEXT NULL,
    correlation_id TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_candidate_symbol_market_symbol_active
ON research_ops.candidate_symbol (market_code, symbol, status)
WHERE status IN ('new','monitoring','needs_more_evidence','promotion_pending');

CREATE INDEX IF NOT EXISTS idx_candidate_symbol_status_score
ON research_ops.candidate_symbol (status, discovery_score DESC, last_seen_at DESC);

CREATE TABLE IF NOT EXISTS research_ops.related_symbol_edge (
    edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_code TEXT NOT NULL,
    source_symbol TEXT NOT NULL,
    target_symbol TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK (relation_type IN (
        'competitor','supplier','customer','peer','sector','holding','index_member','macro_proxy','ownership'
    )),
    confidence NUMERIC(5,4) NOT NULL DEFAULT 0.5000,
    provenance_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_validated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (market_code, source_symbol, target_symbol, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_related_symbol_edge_source
ON research_ops.related_symbol_edge (market_code, source_symbol, confidence DESC);

CREATE INDEX IF NOT EXISTS idx_related_symbol_edge_target
ON research_ops.related_symbol_edge (market_code, target_symbol, confidence DESC);

CREATE TABLE IF NOT EXISTS research_ops.research_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_type TEXT NOT NULL CHECK (target_type IN (
        'research_case','research_brief','candidate_symbol','symbol_dossier'
    )),
    target_id UUID NOT NULL,
    feedback_kind TEXT NOT NULL CHECK (feedback_kind IN (
        'operator_accept','operator_reject','operator_note','postmortem_link','chat_correction'
    )),
    feedback_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_research_feedback_target
ON research_ops.research_feedback (target_type, target_id, created_at DESC);

-- Suggested outbox event types (to be emitted by service layer):
-- research_case.created
-- research_case.updated
-- research_brief.refreshed
-- candidate_symbol.created
-- candidate_symbol.promoted
-- candidate_symbol.rejected
-- symbol_dossier.updated
-- source_bundle.recommended
