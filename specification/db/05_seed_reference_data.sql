-- Representative seeds

INSERT INTO core.role (role_code, display_name)
VALUES
  ('viewer', 'Viewer'),
  ('operator', 'Operator'),
  ('trader_admin', 'Trader Admin'),
  ('platform_admin', 'Platform Admin')
ON CONFLICT (role_code) DO NOTHING;

INSERT INTO core.event_type_registry (event_type_code, display_name, event_family, status)
VALUES
  ('earnings_beat', 'Earnings Beat', 'corporate', 'active'),
  ('guidance_cut', 'Guidance Cut', 'corporate', 'active'),
  ('macro_release', 'Macro Release', 'macro', 'active'),
  ('central_bank_comment', 'Central Bank Comment', 'macro', 'active'),
  ('regulatory_action', 'Regulatory Action', 'regulatory', 'active')
ON CONFLICT (event_type_code) DO NOTHING;

INSERT INTO core.reason_code_registry (reason_code, reason_family, display_name, severity)
VALUES
  ('macro_override', 'postmortem', 'Macro override', 'high'),
  ('timing_error', 'postmortem', 'Timing error', 'medium'),
  ('source_gap', 'postmortem', 'Source gap', 'high'),
  ('schema_invalid', 'pipeline', 'Schema invalid', 'high'),
  ('manual_timeout', 'manual_bridge', 'Manual task timeout', 'medium')
ON CONFLICT (reason_code) DO NOTHING;
