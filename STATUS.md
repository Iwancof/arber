# Event Intelligence OS — Status

## All Phases Complete

**Last Updated**: 2026-04-07

## Phase Progress

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 0: Skeleton | **Complete** | プロジェクト構造, DB スキーマ, API 骨格, Grafana シェル |
| Phase 1: Ingest | **Complete** | ORM モデル (54 tables), Source/Market/Event API, Ingest サービス |
| Phase 2: Forecast | **Complete** | Worker Adapter, Forecast/Decision Pipeline, Dossier/Overlay API |
| Phase 3: Manual+Replay | **Complete** | Prompt Bridge, Replay Engine, Postmortem Judge |
| Phase 4: Paper+Live | **Complete** | BrokerAdapter, Order Lifecycle, Kill Switch, Positions |
| Phase 5: Extensibility | **Complete** | Plugin/Schema/FeatureFlag/EventType/Contract Registry API |

## Final Metrics

| カテゴリ | 数量 |
|---------|------|
| DB テーブル | 54 (7 schemas) |
| SQLAlchemy ORM モデル | 54 |
| API ルート | 59 |
| Pydantic スキーマ | 60+ |
| サービス | 7 (ingest, forecast, decision, prompt_bridge, replay, postmortem, execution) |
| アダプター | 4 (WorkerAdapter/MockWorker, BrokerAdapter/MockBroker) |
| テスト | 103 |
| コミット | 6 |

## API Route Summary (59 routes)

### Core (Phase 1)
- GET /v1/health
- GET/POST /v1/markets, GET /v1/markets/{market_code}
- GET/POST /v1/instruments, GET /v1/instruments/{instrument_id}
- GET/POST/PATCH /v1/source-registry, GET /v1/source-registry/{source_code}
- GET/POST /v1/source-registry/{source_code}/endpoints
- GET/POST /v1/source-bundles
- GET /v1/source-candidates, POST approve-provisional, POST promote
- GET /v1/events, GET /v1/events/{event_id}
- POST /v1/ingest/documents

### Forecast (Phase 2)
- GET /v1/forecasts, GET /v1/forecasts/{forecast_id}
- GET /v1/decisions, GET /v1/decisions/{decision_id} (Dossier)
- GET /v1/overlays/{instrument_id}

### Manual+Replay (Phase 3)
- GET/POST /v1/prompt-tasks, GET /v1/prompt-tasks/{id}
- POST /v1/prompt-tasks/{id}/make-visible
- GET/POST /v1/prompt-tasks/{id}/responses
- POST/GET /v1/replay-jobs, GET /v1/replay-jobs/{id}, POST /v1/replay-jobs/{id}/run
- GET /v1/postmortems, GET /v1/postmortems/{id}
- GET /v1/outcomes/{forecast_id}

### Execution (Phase 4)
- GET /v1/orders, GET /v1/orders/{id}, GET /v1/orders/{id}/fills
- GET /v1/positions
- GET/POST /v1/kill-switches, POST /v1/kill-switches/{id}/clear

### Extensions (Phase 5)
- GET/POST /v1/feature-flags, PATCH /v1/feature-flags/{flag_code}
- GET/POST /v1/schema-registry
- GET/POST /v1/plugins, POST /v1/plugins/{code}/enable, POST /v1/plugins/{code}/disable
- GET/POST /v1/event-types
- GET/POST /v1/contracts

## Architecture Invariants

1. **レジャー分離** ✅ - raw_document, event, forecast, decision, order, outcome, postmortem
2. **市場/ソース/プロバイダ抽象化** ✅ - market_profile + registry + adapter patterns
3. **Grafana Shell + Plugin** ✅ - provisioning + overlay API + plugin registry
4. **実行モード段階** ✅ - replay → shadow → paper → micro_live → live
5. **LLM提案/Policy決定** ✅ - WorkerAdapter proposes, deterministic policy decides
6. **Kill Switch** ✅ - global/market/strategy/source/broker scopes
7. **追記指向** ✅ - append-only ledgers, corrections via links
8. **契約バージョニング** ✅ - schema_registry + contract_compatibility
9. **プラグイン安全境界** ✅ - plugin_registry with enable/disable lifecycle
10. **Feature Flag** ✅ - rollout_state progression
