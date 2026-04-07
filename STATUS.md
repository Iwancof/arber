# Event Intelligence OS — Status

## Current Phase: Phase 2 (Forecast & Decision) - Complete

**Last Updated**: 2026-04-07

## Phase Progress

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 0: Skeleton | **Complete** | プロジェクト構造, DB スキーマ, API 骨格, Grafana シェル |
| Phase 1: Ingest | **Complete** | ORM モデル, API エンドポイント, ソースレジストリ, 取込サービス |
| Phase 2: Forecast | **Complete** | Worker Adapter, Forecast/Decision サービス, Dossier/Overlay API |
| Phase 3: Manual+Replay | Not Started | プロンプトコンソール, リプレイエンジン |
| Phase 4: Paper+Live | Not Started | ブローカーアダプター, 実行モード |
| Phase 5: Extensibility | Not Started | プラグインレジストリ, スキーマレジストリ強化 |

## Phase 2 Deliverables

### Worker Adapter (ADR-004)
- [x] WorkerAdapter ABC (health, execute, adapter_code, supported_task_types)
- [x] WorkerTask / WorkerResult 統一契約 (dataclass)
- [x] MockWorkerAdapter (決定的リプレイ用、SHA-256 ベースの擬似予測)

### サービス層
- [x] Forecast Pipeline (retrieval → worker → reasoning trace → forecast + horizons)
- [x] Decision Policy (score 計算, action 決定, status 設定, risk gates)
- [x] Retrieval Set 構築 (v1: simple rule-based)

### Pydantic スキーマ
- [x] ReasoningTraceRead, RetrievalSetRead/ItemRead
- [x] ForecastLedgerRead (with horizons), ForecastHorizonRead, ForecastList
- [x] DecisionLedgerRead (with reasons), DecisionReasonRead, DecisionList
- [x] DossierRead (aggregate: decision+forecast+event+trace+prompts+orders+outcomes)
- [x] OverlayPayload (ForecastBand, OverlayAnnotation, DecisionInterval)

### API エンドポイント (26 ルート合計)
- [x] GET /v1/forecasts, GET /v1/forecasts/{forecast_id}
- [x] GET /v1/decisions
- [x] GET /v1/decisions/{decision_id} (Dossier aggregate)
- [x] GET /v1/overlays/{instrument_id} (Grafana panel data)

### テスト (46/46 passed)
- [x] Worker adapter テスト (9: 健全性, 決定性, ホライズン生成)
- [x] Decision policy テスト (13: スコア計算, アクション決定, ステータス)
- [x] Forecast スキーマテスト (6: Pydantic バリデーション)
- [x] Phase 1 テスト全維持 (17)
- [x] ルート登録テスト更新 (26 ルート)

## Architecture Summary

- **Backend**: Python 3.14 / FastAPI / SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL 16 (7 schemas, 54 tables)
- **Cache/Queue**: Redis 7
- **UI**: Grafana 11 (shell + custom plugins)
- **Worker**: Adapter pattern (ABC + MockWorkerAdapter)
- **Policy**: Deterministic scoring (v1_simple policy version)
- **Testing**: pytest 46 tests, ruff lint

## Key Design Decisions (Phase 2)

1. **LLM は提案、Policy が決定**: Worker は forecast を生成、deterministic policy が action を決定
2. **MockWorkerAdapter**: SHA-256 ハッシュベースの決定的出力でリプレイモードを支援
3. **Dossier = 中央ビュー**: decision → forecast → event → trace → prompts → orders → outcomes を集約
4. **Overlay = Grafana データ**: forecast_bands + annotations + decision_intervals をチャート用に提供
5. **Policy v1**: シンプルな閾値ベース (将来は policy_pack_registry で拡張)
