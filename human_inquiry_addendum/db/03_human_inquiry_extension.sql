-- 03_human_inquiry_extension.sql
-- Addendum 18: Human Inquiry Orchestration / Question Ops

CREATE SCHEMA IF NOT EXISTS human_ops;

CREATE TABLE IF NOT EXISTS human_ops.inquiry_case (
    inquiry_case_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    market_profile_code text NOT NULL,
    linked_entity_type text NOT NULL CHECK (linked_entity_type IN ('event','decision','position','source_candidate','postmortem','watchlist_item','market_regime')),
    linked_entity_id uuid NULL,
    inquiry_kind text NOT NULL CHECK (inquiry_kind IN (
        'pretrade_decision',
        'position_reassessment',
        'novel_event_interpretation',
        'source_gap_investigation',
        'postmortem_labeling',
        'prompt_reformat_request',
        'market_regime_call',
        'watchlist_reprioritization'
    )),
    dedupe_key text NOT NULL,
    title text NOT NULL,
    benchmark_symbol text NULL,
    primary_symbol text NULL,
    horizon_code text NULL,
    priority_score numeric(10,6) NOT NULL DEFAULT 0,
    urgency_class text NOT NULL CHECK (urgency_class IN ('low','normal','high','critical')),
    case_status text NOT NULL CHECK (case_status IN ('open','monitoring','resolved','canceled')) DEFAULT 'open',
    opened_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    created_trace_id text NULL,
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (market_profile_code, inquiry_kind, dedupe_key, case_status)
);

CREATE TABLE IF NOT EXISTS human_ops.inquiry_signal (
    inquiry_signal_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    inquiry_case_id uuid NULL REFERENCES human_ops.inquiry_case(inquiry_case_id),
    signal_type text NOT NULL CHECK (signal_type IN (
        'high_materiality_low_confidence',
        'macro_single_name_conflict',
        'novel_event_type',
        'source_gap_detected',
        'policy_blocked_need_context',
        'position_monitoring_reassessment',
        'postmortem_needs_human_label',
        'schema_invalid_repeated',
        'market_regime_shift',
        'manual_watchlist_item'
    )),
    signal_score numeric(10,6) NOT NULL DEFAULT 0,
    source_ref_type text NULL,
    source_ref_id uuid NULL,
    observed_at timestamptz NOT NULL DEFAULT now(),
    explanation_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS human_ops.inquiry_task (
    inquiry_task_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    inquiry_case_id uuid NOT NULL REFERENCES human_ops.inquiry_case(inquiry_case_id),
    revision_no integer NOT NULL,
    prompt_task_id uuid NULL REFERENCES forecasting.prompt_task(prompt_task_id),
    task_status text NOT NULL CHECK (task_status IN (
        'draft','visible','claimed','awaiting_response','submitted','parsed',
        'accepted','rejected','expired','superseded','canceled'
    )) DEFAULT 'draft',
    priority_score numeric(10,6) NOT NULL DEFAULT 0,
    sla_class text NOT NULL CHECK (sla_class IN ('slow','normal','fast','urgent')),
    deadline_at timestamptz NOT NULL,
    claim_expires_at timestamptz NULL,
    prompt_pack_hash text NULL,
    evidence_bundle_hash text NULL,
    question_title text NOT NULL,
    question_text text NOT NULL,
    required_schema_name text NOT NULL,
    required_schema_version text NOT NULL,
    bounded_evidence_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    acceptance_rules_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    supersedes_inquiry_task_id uuid NULL REFERENCES human_ops.inquiry_task(inquiry_task_id),
    primary_response_id uuid NULL,
    created_by uuid NULL REFERENCES core.app_user(user_id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (inquiry_case_id, revision_no)
);

CREATE INDEX IF NOT EXISTS idx_inquiry_task_status_deadline ON human_ops.inquiry_task (task_status, deadline_at);
CREATE INDEX IF NOT EXISTS idx_inquiry_task_case ON human_ops.inquiry_task (inquiry_case_id, revision_no DESC);

CREATE TABLE IF NOT EXISTS human_ops.inquiry_assignment (
    inquiry_assignment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    inquiry_task_id uuid NOT NULL REFERENCES human_ops.inquiry_task(inquiry_task_id),
    assigned_user_id uuid NULL REFERENCES core.app_user(user_id),
    assignment_mode text NOT NULL CHECK (assignment_mode IN ('shared','exclusive')),
    assignment_status text NOT NULL CHECK (assignment_status IN ('assigned','claimed','released','expired','completed')) DEFAULT 'assigned',
    assigned_at timestamptz NOT NULL DEFAULT now(),
    claim_until timestamptz NULL,
    released_at timestamptz NULL,
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS human_ops.inquiry_presence (
    inquiry_presence_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES core.app_user(user_id),
    availability_state text NOT NULL CHECK (availability_state IN ('online','busy','away','off_shift')),
    focus_mode text NOT NULL CHECK (focus_mode IN ('none','review','trading','postmortem')),
    can_receive_push boolean NOT NULL DEFAULT true,
    can_receive_urgent boolean NOT NULL DEFAULT true,
    timezone_name text NULL,
    working_hours_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id)
);

CREATE TABLE IF NOT EXISTS human_ops.inquiry_response (
    inquiry_response_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    inquiry_task_id uuid NOT NULL REFERENCES human_ops.inquiry_task(inquiry_task_id),
    submitted_by uuid NULL REFERENCES core.app_user(user_id),
    response_channel text NOT NULL CHECK (response_channel IN ('direct_answer','external_llm','api_import')),
    model_name_user_entered text NULL,
    response_status text NOT NULL CHECK (response_status IN ('received','parsed','valid','invalid','accepted','rejected','late')) DEFAULT 'received',
    submitted_at timestamptz NOT NULL DEFAULT now(),
    raw_response text NOT NULL,
    parsed_json jsonb NULL,
    schema_valid boolean NOT NULL DEFAULT false,
    parser_version text NULL,
    evidence_refs_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    notes text NULL
);

CREATE INDEX IF NOT EXISTS idx_inquiry_response_task ON human_ops.inquiry_response (inquiry_task_id, submitted_at DESC);

CREATE TABLE IF NOT EXISTS human_ops.inquiry_resolution (
    inquiry_resolution_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    inquiry_task_id uuid NOT NULL REFERENCES human_ops.inquiry_task(inquiry_task_id),
    inquiry_response_id uuid NULL REFERENCES human_ops.inquiry_response(inquiry_response_id),
    resolution_status text NOT NULL CHECK (resolution_status IN ('accepted','rejected','partial','late_ignored','stale','superseded')),
    effective_weight numeric(10,6) NULL,
    used_for_decision boolean NOT NULL DEFAULT false,
    affects_decision_id uuid NULL REFERENCES forecasting.decision_ledger(decision_id),
    resolution_reason_codes jsonb NOT NULL DEFAULT '[]'::jsonb,
    resolved_by uuid NULL REFERENCES core.app_user(user_id),
    resolved_at timestamptz NOT NULL DEFAULT now(),
    notes text NULL
);

CREATE TABLE IF NOT EXISTS human_ops.inquiry_metric_snapshot (
    inquiry_metric_snapshot_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_at timestamptz NOT NULL DEFAULT now(),
    open_count integer NOT NULL DEFAULT 0,
    due_soon_count integer NOT NULL DEFAULT 0,
    overdue_count integer NOT NULL DEFAULT 0,
    supersede_rate numeric(10,6) NULL,
    response_latency_p50_sec numeric(12,3) NULL,
    response_latency_p95_sec numeric(12,3) NULL,
    accept_rate numeric(10,6) NULL,
    late_response_rate numeric(10,6) NULL,
    manual_uplift_score_delta numeric(10,6) NULL,
    details_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

ALTER TABLE human_ops.inquiry_task
    ADD CONSTRAINT fk_inquiry_task_primary_response
    FOREIGN KEY (primary_response_id) REFERENCES human_ops.inquiry_response(inquiry_response_id);

CREATE OR REPLACE VIEW human_ops.vw_inquiry_tray AS
SELECT
    it.inquiry_task_id,
    ic.inquiry_case_id,
    ic.inquiry_kind,
    ic.market_profile_code,
    ic.primary_symbol,
    ic.benchmark_symbol,
    it.task_status,
    it.priority_score,
    it.sla_class,
    it.deadline_at,
    it.question_title,
    CASE
        WHEN it.deadline_at < now() THEN 'overdue'
        WHEN it.deadline_at < now() + interval '15 minutes' THEN 'due_soon'
        ELSE 'normal'
    END AS time_bucket
FROM human_ops.inquiry_task it
JOIN human_ops.inquiry_case ic ON ic.inquiry_case_id = it.inquiry_case_id
WHERE it.task_status IN ('visible','claimed','awaiting_response','submitted','parsed');

