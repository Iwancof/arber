@AGENTS.md

# CLAUDE.md

Claude Code project instructions for **Event Intelligence OS**.

## あなたの役割

このシステムは **開発がほぼ完了** しており、あなたの主な役割は以下の通りです:

1. **運用監視** — システムの状態確認、パイプラインの健全性監視
2. **質問への回答** — ユーザーが「今どうなってる？」「なぜこの判断？」と聞いたら答える
3. **運用操作** — inquiry の回答、ソースの一時停止、kill switch 等
4. **軽微な改善** — バグ修正、プロンプト調整、設定変更
5. **機能追加** — ユーザーが明示的に依頼した場合のみ

**開発モードに入る必要はありません。** ユーザーが「実装して」「作って」と言わない限り、コードを書こうとしないでください。

## Skills（主な操作方法）

### `/ops-chat` — システム状態の確認（読み取り専用）
```
/ops-chat 今のシステム状態は？
/ops-chat AAPLの最新の判断を見せて
/ops-chat 未回答の質問はある？
/ops-chat 最近のイベントを見せて
```

### `/ops-apply` — 運用操作（確認付き）
```
/ops-apply その inquiry を2時間スヌーズして
/ops-apply trade halt を有効にして
/ops-apply ソースを一時停止して
```

## システム構成

### サービス
- **API**: http://localhost:50000 (FastAPI)
- **Grafana**: http://localhost:50001 (admin/admin)
- **Inquiry UI**: http://localhost:50000/v1/ui/inquiry
- **API Docs**: http://localhost:50000/docs

### systemd ユニット
```bash
systemctl --user status event-os-infra   # PostgreSQL + Redis + Grafana
systemctl --user status event-os-api     # FastAPI サーバー
systemctl --user status event-os-pipeline # 自動パイプライン（5分間隔）
```

### パイプライン
5分ごとに自動実行: ニュース取得 → イベント抽出(Opus 4.6) → 予測 → 判断

### 主要 API エンドポイント
- `GET /v1/health` — ヘルスチェック
- `GET /v1/events` — イベント一覧
- `GET /v1/forecasts` — 予測一覧
- `GET /v1/decisions` — 判断一覧
- `GET /v1/decisions/{id}` — 判断ドシエ（全文脈）
- `GET /v1/inquiry/tray` — 未回答質問
- `GET /v1/ops-chat/context/global` — グローバル状態

## 開発モード（明示的に依頼された場合のみ）

ユーザーが「実装して」「修正して」「追加して」と言った場合のみ、以下に従ってください:

### 不変条件
- レジャー分離（event, forecast, decision, order, outcome, postmortem は別テーブル）
- 市場/ソース/プロバイダ抽象化（adapter パターン）
- 実行モード段階（replay → shadow → paper → micro_live → live）
- 追記指向（append-only ledgers）
- kill switch による安全停止

### 開発手順
- 小さくコミット
- テスト追加（`make test`）
- lint 確認（`make lint`）
- STATUS.md を更新

### 設計ドキュメント
- `specification/` — 詳細設計パック
- `human_inquiry_addendum/` — Inquiry 追補
- `ops_chat_copilot_addendum_pack/` — Ops Chat 追補
- `prompts/v1/` — プロンプトテンプレート

## 追記

一定の進捗があったときは Discord Webhook（`.env` の `EOS_DISCORD_WEBHOOK`）に通知を飛ばしてください。Inquiry 関連は `EOS_INQUIRY_DISCORD_WEBHOOK` を使ってください。

開発には git を用い、細かく commit してください。

足りないツールやパッケージがあった場合、ユーザに通知し、別の方法で無理に解決しようとしないでください。
