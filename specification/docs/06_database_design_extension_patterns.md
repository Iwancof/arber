# 06. Database Design Extension Patterns

## 6.1 目的

この文書は「新しい市場・ソース・worker・plugin・schema を追加しても DB が破綻しないこと」を主眼にする。

## 6.2 Registry Pattern

### 適用対象
- market profiles
- event types
- reason codes
- schemas
- plugins
- worker adapters
- broker adapters
- policy packs

### 方針
registry は「存在一覧」だけでなく、最低でも次を持つ。

- code
- display_name
- version
- status
- capability tags
- compatibility hints
- rollout state
- owner/team

## 6.3 Versioned Payload Pattern

すべての JSON payload は次を持つ。

- `schema_name`
- `schema_version`
- `payload_version`
- `created_by_component`
- `created_by_version`

例:
- event_json
- forecast_json
- reasoning_trace_json
- prompt_response.parsed_json
- plugin manifest

## 6.4 Polymorphic Link Pattern

retrieval_item や evidence_link は複数種類の target を指したい。  
2 方式がある。

1. separate nullable FK
2. `(target_kind, target_id)` polymorphic key

v1 ではアプリケーション整合性込みで `target_kind + target_id` を採用してよい。  
ただし、重要 ledger では query performance のために冗長列を持つ。

## 6.5 Registry + Snapshot Pattern

plugin registry, source registry, worker registry は mutable である。  
一方、forecast/decision は実行時点の環境を固定したい。  
そのため、ledger には registry の参照だけでなく **snapshot columns** を持つ。

例:
- worker_adapter_code + worker_adapter_version_snapshot
- prompt_template_id + prompt_version_snapshot
- policy_pack_code + policy_pack_version_snapshot
- source_bundle_code + bundle_version_snapshot

## 6.6 Soft-State vs Immutable-State

### Immutable
- raw_document body
- event_json
- forecast_json
- decision basis
- prompt_response.raw_response
- postmortem verdict

### Soft-state
- current watcher health
- current plugin enabled flag
- current source status
- current broker connection status

Soft-state は snapshot table or cache に置く。

## 6.7 Partitioning Strategy

時系列で膨らむ表は partition 対象。

- raw_document (月次)
- event_ledger (月次)
- forecast_ledger (月次)
- decision_ledger (月次)
- order_ledger (月次)
- outcome_ledger (月次)
- audit_log (月次)

### 理由
- retention 管理
- index サイズの抑制
- replay 範囲抽出の効率化

## 6.8 Rollup / Snapshot Pattern

Grafana と operator UI の高速表示のため、重い join を毎回しない。

作るべき rollup:
- source contribution daily
- reliability by model/source/event/horizon
- current open decisions
- current prompt task queue
- current position and exposure
- recent source gap by sector/market

## 6.9 Migration-friendly Enum Strategy

### 避けるもの
- DB enum の乱用
- アプリ側固定 enum のみ

### 推奨
- registry table + check constraint の併用
- high-value fields だけ check で守る
- 新値追加時は migration + registry entry + schema update を同時に行う

## 6.10 Cross-market Extensibility

新市場追加時に DB へ必要なのは:

- market_profile row
- instrument rows
- benchmark_map
- source bundle rows
- source endpoint rows
- session template / language / currency / calendar rules

core schema 自体を変えなくてよいことが理想。

## 6.11 Multi-environment Readiness

本番/検証/開発環境は DB を分離するのが基本。  
同一 DB 内で `env_code` を持つ設計は v1 では採らない。  
ただし、`execution_mode_state` や ledger には `environment_label` を残してもよい。

## 6.12 Future Multi-tenant Readiness

v1 では single-tenant でよい。  
ただし、tenant 化するなら次が境界になる。

- app_user / roles
- plugin settings
- source bundles
- market_profile visibility
- broker account binding

この可能性のため、`owner_scope_json` を registry tables に持たせる余地を残す。
