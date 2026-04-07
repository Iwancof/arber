# Event Intelligence OS — Status

## Current Phase: Phase 0 (Skeleton)

**Last Updated**: 2026-04-07

## Phase Progress

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 0: Skeleton | **In Progress** | プロジェクト構造, DB スキーマ, API 骨格, Grafana シェル |
| Phase 1: Ingest | Not Started | ソースレジストリ, ウォッチプランナー, raw_document 取込 |
| Phase 2: Forecast | Not Started | リトリーバル, 予測ワーカー, 判断レジャー |
| Phase 3: Manual+Replay | Not Started | プロンプトコンソール, リプレイエンジン |
| Phase 4: Paper+Live | Not Started | ブローカーアダプター, 実行モード |
| Phase 5: Extensibility | Not Started | プラグインレジストリ, スキーマレジストリ強化 |

## Phase 0 Tasks

- [x] Git リポジトリ初期化
- [x] プロジェクト構造 (backend/, tests/, db/, grafana/)
- [x] pyproject.toml + .gitignore
- [x] Makefile (標準コマンド群)
- [x] docker-compose.yml (PostgreSQL 16 + Redis 7 + Grafana 11)
- [x] DB スキーマ SQL (7 スキーマ, 47+ テーブル)
- [x] FastAPI バックエンド骨格 (ヘルスチェック API)
- [x] Grafana プロビジョニング (データソース + ダッシュボード)
- [x] テスト基盤 (pytest + conftest)
- [x] STATUS.md
- [ ] 検証 (lint, typecheck, test)
- [ ] 初回コミット

## Architecture Summary

- **Backend**: Python 3.12 / FastAPI / SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL 16 (7 schemas: core, sources, content, forecasting, execution, feedback, ops)
- **Cache/Queue**: Redis 7
- **UI**: Grafana 11 (shell + custom plugins)
- **Testing**: pytest + httpx

## Key Invariants

1. レジャー分離: event, forecast, decision, order, outcome, postmortem は別テーブル
2. 市場/ソース/プロバイダ抽象化: market_profile + registry + adapter パターン
3. Grafana Shell + Plugin アーキテクチャ
4. 実行モード段階: replay → shadow → paper → micro_live → live
5. 追記指向: レジャーは append-only、修正は新行+リンク
6. 契約バージョニング: 全 JSON ペイロードに schema_version
