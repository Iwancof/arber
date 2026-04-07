# 12. LLM Workers, Manual Bridge, and Reasoning Trace

## 12.1 目的

LLM は 1 種類ではない。  
API model, CLI model, human-operated web model を同じ上位契約で扱う。  
そのために worker adapter abstraction を置く。

## 12.2 Worker Types

- API worker
- CLI/headless worker
- manual expert bridge
- future: ensemble worker, heuristic worker, sandbox worker

## 12.3 Worker Task Contract

共通で必要なもの:
- task_type
- schema_name
- schema_version
- prompt_template_id
- prompt_version
- input_payload
- evidence_refs
- timeout_sec
- mode
- determinism_hint

## 12.4 Worker Result Contract

- raw_text
- parsed_json
- schema_valid
- parse_errors
- worker_metadata
- token/latency estimates if available
- reasoning_trace_summary
- output_hash

## 12.5 Task Types

- event_extract
- macro_regime_assess
- single_name_forecast
- skeptic_review
- judge_postmortem
- source_scout
- prompt_pack_generate
- manual_reformat

## 12.6 Structured Output First

raw text is secondary。  
判定に使うのは parsed JSON のみ。  
free text は summary / notes のみに限定する。

## 12.7 Reasoning Trace

保存するのは provider raw CoT ではなく、構造化 reasoning trace。

### 必須字段
- hypotheses
- selected_hypothesis
- rejected_hypotheses
- counterarguments
- risk_flags
- evidence_refs
- confidence_before
- confidence_after
- trace_version

### 目的
- 可視化しやすい
- 比較しやすい
- provider が変わっても扱いやすい
- chain-of-thought の生テキスト依存を避ける

## 12.8 Prompt Versioning

prompt はソースコード同等に管理する。

- prompt_template_id
- semantic_version
- rollout_state
- owner
- target_schema
- deprecated_at
- changelog

ledger には必ず snapshot を残す。

## 12.9 Manual Expert Bridge

### 発動条件
- materiality high
- confidence low
- new event type
- macro and single-name conflict
- large position or live impact

### ルール
- critical path 必須にしない
- bounded evidence only
- schema validation mandatory
- deadline required
- manual model reliability tracked

## 12.10 Manual Model Reliability

集計粒度:
- model_name
- task_type
- market_profile
- sector
- horizon
- event_type

指標:
- schema_valid_rate
- accepted_rate
- hit_rate
- brier
- avg decision uplift
- avg operator delay

## 12.11 CLI Worker 運用

CLI/headless worker に必要:
- stable stdout JSON
- timeout
- retries
- artifact retention
- environment isolation
- prompt / result capture

## 12.12 Ensemble / Provider Routing (future)

将来は worker router を追加できる。  
ただし v1 は単純でよい。

- primary worker
- fallback worker
- manual bridge optional

## 12.13 Failure Modes

- schema invalid
- prompt template mismatch
- evidence ref unknown
- timeout
- provider unavailable
- operator pasted freeform essay
- stale response after deadline

各 failure は distinct reason code を持つ。
