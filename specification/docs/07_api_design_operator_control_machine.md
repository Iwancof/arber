# 07. API Design — Operator / Control / Machine

## 7.1 API 層の分け方

### Operator API
人間が使う画面向け。  
Decision Dossier, Prompt Console, Source Candidate Review など。

### Control API
registry, watch plan, feature flags, live mode, plugin settings などの制御面。

### Machine API
watcher, workflow, worker, broker adapter など内部機械同士のやり取り。

## 7.2 設計原則

- JSON over HTTPS
- RFC3339 UTC timestamps
- trace_id を全レスポンスに含める
- POST の一部は idempotency key 必須
- long-running task は job resource を返す
- optimistic concurrency for mutable registry records
- API version は URI + schema version の二重で管理

## 7.3 共通レスポンス

### Query response
```json
{
  "items": [],
  "next_cursor": "opaque",
  "trace_id": "..."
}
```

### Mutating response
```json
{
  "id": "....",
  "status": "accepted",
  "trace_id": "..."
}
```

### Error
problem+json 風を採用。

## 7.4 Query API

- `GET /v1/markets`
- `GET /v1/instruments`
- `GET /v1/events`
- `GET /v1/events/{event_id}`
- `GET /v1/forecasts`
- `GET /v1/forecasts/{forecast_id}`
- `GET /v1/decisions`
- `GET /v1/decisions/{decision_id}`
- `GET /v1/prompt-tasks`
- `GET /v1/source-registry`
- `GET /v1/source-candidates`
- `GET /v1/postmortems`
- `GET /v1/plugins`
- `GET /v1/reliability`
- `GET /v1/overlays/{instrument_id}`

## 7.5 Command API

- `POST /v1/prompt-tasks`
- `POST /v1/prompt-tasks/{task_id}/responses`
- `POST /v1/prompt-tasks/{task_id}/accept`
- `POST /v1/prompt-tasks/{task_id}/reject`
- `POST /v1/source-candidates/{id}/approve-provisional`
- `POST /v1/source-candidates/{id}/promote`
- `POST /v1/replay-jobs`
- `POST /v1/watch-plans/recompute`
- `POST /v1/live/arm`
- `POST /v1/live/disarm`
- `POST /v1/kill-switches/{scope}/activate`
- `POST /v1/plugins/{plugin_code}/enable`
- `POST /v1/plugins/{plugin_code}/disable`

## 7.6 Machine API

- `POST /internal/v1/worker-tasks`
- `POST /internal/v1/worker-results`
- `POST /internal/v1/broker-intents`
- `POST /internal/v1/outbox/publish`
- `POST /internal/v1/watchers/heartbeat`
- `POST /internal/v1/watchers/documents`
- `POST /internal/v1/events/verify`
- `POST /internal/v1/outcomes/build`

## 7.7 Streaming

必要な stream:
- prompt task updates
- decision status updates
- order state updates
- watcher health alerts
- replay job progress

v1 は SSE でよい。  
将来必要なら WebSocket へ拡張。

## 7.8 認可

### Role base
- viewer
- operator
- trader_admin
- platform_admin

### Resource scope
- market_profile
- plugin
- environment
- source candidate
- broker account

## 7.9 API Versioning

### 原則
- breaking changes -> `/v2`
- non-breaking additions -> same URI + schema update
- payload schema version は body にも持つ

### 互換期間
- 旧 API は deprecation grace period を設ける
- worker adapters は compatibility matrix を持つ

## 7.10 Overlay API

UI のための専用集約 API を持つ。  
生テーブルを直接 UI にさらしすぎない。

例:
`GET /v1/overlays/{instrument_id}?from=...&to=...&horizon=5d`

返すもの:
- bars
- forecast bands
- barrier lines
- event annotations
- prompt annotations
- decision state intervals
- order markers
- position intervals

## 7.11 Plugin API

Grafana plugin は次の facade を叩く。

- `/v1/plugins/config`
- `/v1/plugins/navigation`
- `/v1/plugins/panels/{panel_code}/data`
- `/v1/plugins/actions/{action_code}`

plugin は domain writes を直接行わず、action facade を経由する。

## 7.12 Audit 要件

次の操作は必ず audit log:
- live arm/disarm
- kill switch
- prompt accept/reject
- source candidate promotion
- source disable
- plugin enable/disable
- manual note on decision
