# Event Intelligence OS — Status

## Current Phase: Phase 1 (Ingest Pipeline) - Complete

**Last Updated**: 2026-04-07

## Phase Progress

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 0: Skeleton | **Complete** | プロジェクト構造, DB スキーマ, API 骨格, Grafana シェル |
| Phase 1: Ingest | **Complete** | ORM モデル, API エンドポイント, ソースレジストリ, 取込サービス |
| Phase 2: Forecast | Not Started | リトリーバル, 予測ワーカー, 判断レジャー |
| Phase 3: Manual+Replay | Not Started | プロンプトコンソール, リプレイエンジン |
| Phase 4: Paper+Live | Not Started | ブローカーアダプター, 実行モード |
| Phase 5: Extensibility | Not Started | プラグインレジストリ, スキーマレジストリ強化 |

## Phase 1 Deliverables

### SQLAlchemy ORM モデル (54 テーブル, 7 スキーマ)
- [x] core: AppUser, Role, MarketProfile, Instrument, TradingVenue, BenchmarkMap, InstrumentAlias
- [x] sources: SourceRegistry, SourceEndpoint, SourceBundle, WatchPlan, SourceCandidate, UniverseSet
- [x] content: RawDocument, DedupCluster, EventLedger, EventAssetImpact, EventEvidenceLink
- [x] forecasting: ForecastLedger, DecisionLedger, PromptTask, ReasoningTrace, PolicyPackRegistry
- [x] execution: OrderLedger, ExecutionFill, PositionSnapshot
- [x] feedback: OutcomeLedger, PostmortemLedger, ReliabilityStat
- [x] ops: AuditLog, KillSwitch, WatcherInstance, OutboxEvent, JobRun
- [x] extensions: FeatureFlag, SchemaRegistryEntry, EventTypeRegistry, PluginRegistry

### Pydantic API スキーマ
- [x] MarketProfileRead/Create/List, InstrumentRead/Create/List
- [x] SourceRegistryRead/Create/Update/List, SourceEndpointRead/Create, SourceBundleRead/Create
- [x] EventLedgerRead/List, EventDetailRead, RawDocumentRead
- [x] PaginatedResponse, OrmBase

### API エンドポイント (21 ルート)
- [x] GET /v1/health
- [x] GET/POST /v1/markets, GET /v1/markets/{market_code}
- [x] GET/POST /v1/instruments, GET /v1/instruments/{instrument_id}
- [x] GET/POST/PATCH /v1/source-registry, GET /v1/source-registry/{source_code}
- [x] GET/POST /v1/source-registry/{source_code}/endpoints
- [x] GET/POST /v1/source-bundles
- [x] GET /v1/source-candidates, POST approve-provisional, POST promote
- [x] GET /v1/events, GET /v1/events/{event_id}
- [x] POST /v1/ingest/documents

### サービス層
- [x] Ingest service (SHA-256 dedup, content_hash + native_doc_id 重複検出)

### テスト (17/17 passed)
- [x] モデル登録テスト (54 テーブル, 7 スキーマ, レジャー分離)
- [x] Pydantic スキーマテスト (デフォルト値, partial update, ORM mode)
- [x] API ルートテスト (21 ルート登録)
- [x] Ingest サービステスト (ハッシュ関数)
- [x] ヘルスチェックテスト
- [x] 設定テスト

## Architecture Summary

- **Backend**: Python 3.14 / FastAPI / SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL 16 (7 schemas: core, sources, content, forecasting, execution, feedback, ops)
- **Cache/Queue**: Redis 7
- **UI**: Grafana 11 (shell + custom plugins)
- **Testing**: pytest + httpx (17 tests)
- **Code Quality**: ruff (lint+format), mypy (strict)

## Key Invariants

1. レジャー分離: event, forecast, decision, order, outcome, postmortem は別テーブル
2. 市場/ソース/プロバイダ抽象化: market_profile + registry + adapter パターン
3. Grafana Shell + Plugin アーキテクチャ
4. 実行モード段階: replay → shadow → paper → micro_live → live
5. 追記指向: レジャーは append-only、修正は新行+リンク
6. 契約バージョニング: 全 JSON ペイロードに schema_version
