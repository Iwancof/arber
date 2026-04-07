# ベンダー・運用方針の選定依頼

**宛先**: 設計担当者
**発信**: 実装チーム
**日付**: 2026-04-07
**件名**: パイプライン実装に必要なベンダー・運用判断のリクエスト

---

## 背景

Event Intelligence OS の基盤実装（Phase 0-5 + 安全性強化）が完了しました。

- DB 54テーブル / API 59ルート / テスト 158 / サービス 7 / アダプター 4
- 実行モード3層安全ガード / JWT認証 / Outbox / Kill Switch 5スコープ

現在、**全てのアダプターインターフェースとパイプライン骨格は存在しますが、実際のデータを流す部分が未接続**です。仕様書はアーキテクチャをベンダー非依存で記述しており、以下の選定判断がないと実装を進められません。

---

## 判断が必要な項目

### 1. LLM プロバイダ（最重要）

イベント抽出（`event_extract`）と予測（`single_name_forecast`）の両方に使用します。

**質問:**
- **v1 で使用する LLM プロバイダは？**（Claude API / OpenAI GPT / Gemini / ローカルモデル / 複数併用）
- 仕様書の Worker Adapter は API / CLI / Manual の3種を想定しています。v1 では API 型のみで十分ですか？
- コスト上限の目安はありますか？（例: 月額 $XXX、1リクエストあたり $X.XX 以内）
- プロンプトテンプレートの初版は実装側で設計して良いですか？それとも設計側から提供されますか？

**実装への影響:**
- 選定後、`WorkerAdapter` の実装体（例: `ClaudeWorkerAdapter`）を作成します
- イベント抽出と予測で別モデル（例: 抽出は Haiku、予測は Sonnet）を使い分ける想定はありますか？

---

### 2. ニュースソース（v1 US Equities 向け）

仕様書は RSS / JSON API / HTML scrape / WebSocket / Calendar 等のアダプタータイプを定義していますが、具体的なソースは未指定です。

**質問:**
- **v1 で接続するニュースソースは？** 以下のような選択肢があります:

| ソース | 種別 | コスト | カバレッジ |
|--------|------|--------|-----------|
| SEC EDGAR RSS | official | 無料 | 米国上場企業の公式開示 |
| Federal Reserve Calendar | official | 無料 | FOMC 等マクロイベント |
| Yahoo Finance RSS | vendor | 無料 | 一般ニュース |
| NewsAPI.org | vendor | $449/月〜 | 広範なニュース集約 |
| Benzinga / Alpha Vantage | vendor | 有料 | リアルタイムニュース |
| Reddit/X(Twitter) | community | API 有料化 | センチメント |

- 無料ソースのみで v1 を開始して良いですか？
- ソースの優先度（まず何を繋ぐか）は？
- ポーリング間隔の目安は？（例: EDGAR は30分毎、一般ニュースは5分毎）

---

### 3. 市場価格データ

Outcome Builder（事後評価）に必要です。予測の「当たったか外れたか」を判定するために、実現リターンを計算する価格データが必要です。

**質問:**
- **株価データのソースは？**

| ソース | コスト | 遅延 | 備考 |
|--------|--------|------|------|
| Yahoo Finance (yfinance) | 無料 | 15分遅延 | 非公式 API、レート制限あり |
| Alpha Vantage | 無料枠あり | リアルタイム〜 | 5 calls/min (無料) |
| Polygon.io | $29/月〜 | リアルタイム | REST + WebSocket |
| ブローカー API | ブローカー依存 | リアルタイム | 口座必要 |

- v1 は日次終値ベースで十分ですか？（リアルタイムは不要？）
- イントラデイの価格追跡は Phase いくつから必要ですか？

---

### 4. ブローカー（Paper → Live）

仕様書は「v1 は単一ブローカー」としています。

**質問:**
- **v1 のブローカーは？**（例: Alpaca / Interactive Brokers / 国内証券 API）
- paper trading 環境があるブローカーが望ましいですが、指定はありますか？
- v1 は Paper モードまでで、Live は Phase いくつから有効化しますか？

---

### 5. 開発・運用に使う LLM ツール

日常的なコード実装・レビュー・運用に使う AI ツールの選定です。

**質問:**
- **主要な実装エージェントは？**（Claude Code / Codex / 併用）
- CLAUDE.md に「Codex を adversarial review や test gap discovery に使う」とありますが、この運用方針は維持しますか？
- CI/CD で LLM を使ったテスト生成やレビューを組み込む予定はありますか？

---

### 6. v1 スコープの確認

**質問:**
- v1 の対象市場は **US Equities のみ** で確定ですか？
- v1 の対象銘柄ユニバースは？（例: S&P 500 / Russell 1000 / 任意指定）
- v1 の実行モードは Paper まで？それとも Micro Live まで？
- v1 のターゲットユーザー数は？（1人 / 小規模チーム / 複数チーム）

---

### 7. インフラ・デプロイ

**質問:**
- 本番環境はどこを想定していますか？（自宅サーバー / VPS / AWS / GCP）
- 現在 systemd user unit で動いていますが、この運用で v1 は十分ですか？
- DB のバックアップ方針は？

---

## 判断のタイムライン

以下の順で選定いただけると、実装をブロックせずに進められます：

1. **即座に必要**: LLM プロバイダ（#1）— これが決まれば Worker Adapter を実装開始
2. **1週間以内**: ニュースソース（#2）+ 価格データ（#3）— パイプラインの入出力
3. **2週間以内**: ブローカー（#4）— Paper 実行開始
4. **随時**: 開発ツール（#5）、スコープ確認（#6）、インフラ（#7）

---

## 補足：現在の実装で「すぐ試せること」

選定を待つ間も、以下は動作可能です：

```bash
# API サーバー起動
systemctl --user start event-os-infra event-os-api

# 手動でドキュメント投入
curl -X POST http://localhost:50000/v1/ingest/documents -H "Content-Type: application/json" -d '{...}'

# Mock Worker でリプレイ実行
curl -X POST http://localhost:50000/v1/replay-jobs -H "Content-Type: application/json" -d '{...}'

# API ドキュメント
open http://localhost:50000/docs

# Grafana ダッシュボード
open http://localhost:50001
```
