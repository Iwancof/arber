# Event Intelligence OS — Status

## Current Phase: Phase 3 (Manual Bridge + Replay) - Complete

**Last Updated**: 2026-04-07

## Phase Progress

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 0: Skeleton | **Complete** | プロジェクト構造, DB スキーマ, API 骨格, Grafana シェル |
| Phase 1: Ingest | **Complete** | ORM モデル, API エンドポイント, ソースレジストリ, 取込サービス |
| Phase 2: Forecast | **Complete** | Worker Adapter, Forecast/Decision サービス, Dossier/Overlay API |
| Phase 3: Manual+Replay | **Complete** | Prompt Bridge, Replay Engine, Postmortem Judge |
| Phase 4: Paper+Live | Not Started | ブローカーアダプター, 実行モード |
| Phase 5: Extensibility | Not Started | プラグインレジストリ, スキーマレジストリ強化 |

## Phase 3 Deliverables

### Prompt Task ライフサイクル
- [x] 状態遷移: created → visible → submitted → parsed → accepted/rejected/expired
- [x] create_prompt_task() - タスク作成 + Decision を waiting_manual に
- [x] transition_task_status() - バリデーション付き状態遷移
- [x] submit_response() - レスポンス送信
- [x] accept_response() - 受理 + Decision を approved に戻す

### Manual Expert Bridge
- [x] should_escalate_to_manual() - エスカレーション判定
- [x] トリガー: novel_event_type, high_materiality_low_confidence, large_position

### Replay Engine
- [x] create_replay_job() - リプレイジョブ作成 (JobRun)
- [x] run_replay() - イベント一括再実行 (forecast + decision pipeline)
- [x] MockWorkerAdapter 使用で決定的リプレイ

### Postmortem / Judge
- [x] record_outcome() - 実現リターン記録
- [x] judge_verdict() - 予測精度判定 (correct/wrong/mixed/insufficient)
- [x] create_postmortem() - Postmortem 生成 + failure_codes
- [x] レビューフラグ: requires_source_review, requires_prompt_review

### API エンドポイント (39 ルート合計, +13)
- [x] GET/POST /v1/prompt-tasks, GET /v1/prompt-tasks/{id}
- [x] POST /v1/prompt-tasks/{id}/make-visible
- [x] GET/POST /v1/prompt-tasks/{id}/responses
- [x] POST/GET /v1/replay-jobs, GET /v1/replay-jobs/{id}
- [x] POST /v1/replay-jobs/{id}/run
- [x] GET /v1/postmortems, GET /v1/postmortems/{id}
- [x] GET /v1/outcomes/{forecast_id}

### テスト (67/67 passed, +21)
- [x] Prompt bridge テスト (6: エスカレーション判定)
- [x] Postmortem judge テスト (8: verdict 判定ロジック)
- [x] Phase 3 スキーマテスト (5: Pydantic バリデーション)
- [x] ルートテスト更新 (39 ルート + メソッド検証)

## Cumulative Progress

| カテゴリ | 数量 |
|---------|------|
| DB テーブル | 54 (7 schemas) |
| API ルート | 39 |
| テスト | 67 |
| サービス | 6 (ingest, forecast, decision, prompt_bridge, replay, postmortem) |
| Adapter | 2 (WorkerAdapter ABC, MockWorkerAdapter) |
| コミット | 4 |
