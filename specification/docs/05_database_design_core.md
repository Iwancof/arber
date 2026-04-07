# 05. Database Design Core

## 5.1 DB 方針

主系ストアは PostgreSQL。理由:

- ledger の整合性
- JSONB による拡張性
- Grafana / SQL 探索との相性
- schema migration と role 管理のしやすさ
- outbox pattern と advisory locks の実装容易性

補助ストア:
- object storage: raw payload, rendered prompt pack, snapshots
- Redis: queues, ephemeral cache, rate limiting
- optional pgvector: retrieval embeddings

## 5.2 Schema 分割

- `core`
- `sources`
- `content`
- `forecasting`
- `execution`
- `feedback`
- `ops`

### 目的
- permission boundary
- migration blast radius reduction
- logical ownership clarity
- future split readiness

## 5.3 主キー戦略

- 内部 PK は `uuid`
- 公開識別子は `*_code` or prefixed ID
- 外部 provider native id は別列で保持
- human-facing reference ids はアプリ層で生成してよい

## 5.4 時刻列

すべて `timestamptz`。  
用途別に分ける。

- `published_at`
- `ingested_at`
- `effective_at`
- `event_time`
- `forecasted_at`
- `decision_at`
- `submitted_at`
- `filled_at`
- `horizon_end_at`

## 5.5 Ledger 分離

### raw_document
真実の一次記録。変更しない。補正は correction link。

### event_ledger
抽出結果。修正時は corrected event row を追加。

### forecast_ledger
予測結果。再計算しても overwrite しない。

### decision_ledger
policy と score の結果。上書きしない。

### order_ledger
broker interaction を忠実に残す。

### outcome_ledger
時間が経ってから確定する結果。

### postmortem_ledger
正誤・原因分析。

## 5.6 主要テーブル群

### core
- app_user
- role
- user_role
- market_profile
- trading_venue
- instrument
- instrument_alias
- benchmark_map
- feature_flag
- schema_registry
- event_type_registry
- reason_code_registry
- plugin_registry
- worker_adapter_registry
- broker_adapter_registry

### sources
- source_registry
- source_endpoint
- source_bundle
- source_bundle_item
- source_candidate
- universe_set
- universe_member
- watch_plan
- watch_plan_item

### content
- raw_document
- dedup_cluster
- document_asset_link
- event_ledger
- event_asset_impact
- event_evidence_link

### forecasting
- retrieval_set
- retrieval_item
- reasoning_trace
- forecast_ledger
- decision_ledger
- prompt_task
- prompt_response
- reliability_snapshot

### execution
- execution_mode_state
- broker_account
- order_ledger
- fill_ledger
- position_snapshot
- position_ledger

### feedback
- outcome_ledger
- judge_run
- postmortem_ledger
- source_gap_stat
- reliability_rollup

### ops
- audit_log
- watcher_instance
- workflow_run
- outbox_event
- system_alert
- kill_switch

## 5.7 Query パターン

### Dossier query
目的: 1 decision を end-to-end で表示  
必要 join:
- forecast -> decision
- event -> evidence
- prompt task/response
- order/fill
- outcome/postmortem
- reasoning trace

### Overlay query
目的: 価格グラフに重ねる  
必要:
- bars
- q10/q50/q90
- barriers
- event timestamps
- prompt task timestamps
- decision statuses
- order timestamps

### Source contribution query
目的: source の寄与を評価  
必要:
- source -> raw_document -> event -> forecast -> outcome

## 5.8 Index 指針

- `(market_profile_id, symbol)` unique on instrument
- `(published_at desc)` on raw_document
- GIN on `coverage_tags_json`, `markets_json`, `metadata_json`
- `(event_type, event_time desc)` on event_ledger
- `(instrument_id, horizon, forecasted_at desc)` on forecast_ledger
- `(decision_status, decision_at desc)` on decision_ledger
- `(task_status, deadline_at)` on prompt_task
- `(source_id, generated_at desc)` on source stats
- `(topic, published_at, status)` on outbox_event

## 5.9 更新ルール

- ledger row の mutable columns を最小化
- status は別テーブル or last-known snapshot で持つ
- big JSON payload は immutable
- metadata_json は additive change のみ
- hard delete は原則禁止、retire/disable/expired を使う

## 5.10 拡張性のための DB 原則

- enum を DB native enum にしすぎない。registry table で逃がす
- market specific policy を table-driven にする
- plugin/adapter を registry 化する
- schema version を payload と row の両方に持つ
- raw text と structured payload を両方保存する
