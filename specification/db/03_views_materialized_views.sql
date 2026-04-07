-- Representative views/materialized views for Grafana and operator APIs

CREATE OR REPLACE VIEW forecasting.vw_decision_dossier AS
SELECT
    d.decision_id,
    d.decided_at,
    d.decision_status,
    d.action,
    d.score,
    d.reason_codes_json,
    f.forecast_id,
    f.forecasted_at,
    f.model_family,
    f.model_version,
    f.prompt_version,
    f.confidence,
    f.instrument_id,
    i.symbol,
    i.display_name,
    ce.event_id,
    ce.event_type,
    ce.event_time
FROM forecasting.decision_ledger d
JOIN forecasting.forecast_ledger f ON f.forecast_id = d.forecast_id
LEFT JOIN content.event_ledger ce ON ce.event_id = f.event_id
LEFT JOIN core.instrument i ON i.instrument_id = f.instrument_id;

CREATE OR REPLACE VIEW forecasting.vw_overlay_annotations AS
SELECT
    'event'::text AS annotation_type,
    ce.event_id::text AS ref_id,
    ce.event_time AS ts,
    ce.event_type AS title,
    ce.direction_hint AS text,
    ce.issuer_instrument_id AS instrument_id
FROM content.event_ledger ce
UNION ALL
SELECT
    'prompt'::text AS annotation_type,
    pt.prompt_task_id::text AS ref_id,
    pt.created_at AS ts,
    pt.task_type AS title,
    pt.status AS text,
    f.instrument_id
FROM forecasting.prompt_task pt
JOIN forecasting.decision_ledger d ON d.decision_id = pt.decision_id
JOIN forecasting.forecast_ledger f ON f.forecast_id = d.forecast_id
UNION ALL
SELECT
    'order'::text AS annotation_type,
    o.order_id::text AS ref_id,
    o.submitted_at AS ts,
    o.side || ' ' || o.order_type AS title,
    o.status AS text,
    o.instrument_id
FROM execution.order_ledger o;

CREATE MATERIALIZED VIEW IF NOT EXISTS feedback.mv_reliability_by_dimension AS
SELECT
    market_profile_id,
    source_id,
    event_type,
    sector,
    horizon_code,
    model_family,
    manual_model_name,
    count(*) AS sample_size,
    avg(hit_rate) AS avg_hit_rate,
    avg(brier) AS avg_brier
FROM feedback.reliability_stat
GROUP BY market_profile_id, source_id, event_type, sector, horizon_code, model_family, manual_model_name;

CREATE INDEX IF NOT EXISTS idx_mv_reliability_dim
    ON feedback.mv_reliability_by_dimension (market_profile_id, event_type, horizon_code);
