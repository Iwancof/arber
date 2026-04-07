# 02. System Context and Non-Functional Requirements

## 2.1 システム境界

Event Intelligence OS は、次を担当する。

- 市場・ニュース・開示・マクロ予定の収集
- 文書からの event extraction
- 過去事例と reliability を用いた予測
- 人間介入タスクの管理
- 意思決定支援とリスクゲート
- execution mode ごとの注文フロー
- 事後評価と source/model/reason code 単位の反省
- Grafana shell 上での可視化・操作

### システム外
- 実際の外部LLMの Web UI
- 外部ブローカー
- 外部ニュースベンダー
- 外部 market data provider
- 外部認証基盤

## 2.2 アクター

- **viewer**: 観測と閲覧
- **operator**: prompt task, source candidate, no-trade override, replay
- **trader_admin**: live mode, broker policy, kill switch
- **platform_admin**: source registry, worker registry, plugin registry, migrations
- **system workers**: watchers, extractors, scorers, routers
- **external manual expert**: operator が経由して使う Web LLM

## 2.3 想定ユースケース

1. 新着ニュースを Event Inbox で triage する  
2. 価格チャート上で予測帯とイベントを重ねて確認する  
3. 重要イベントだけ manual prompt を発行する  
4. source gap が多いセクターで source candidate を承認する  
5. replay で仮説の再検証を行う  
6. paper/live 差分を postmortem から確認する  
7. 新しい市場を追加する  
8. 新しい worker adapter を追加する  
9. 新しい panel plugin を追加する  

## 2.4 NFR の優先順位

### 最重要
- auditability
- reproducibility
- safety
- observability
- bounded blast radius

### 重要
- operator usability
- extension cost
- correctness of contracts
- time-safe replay

### 重要だが v1 では最適化しない
- ultra-low latency
- multi-tenant SaaS
- arbitrary custom scripting by users

## 2.5 モード別要求

| mode | 目的 | 優先事項 |
|---|---|---|
| replay | 検証 | determinism, time-safe availability |
| shadow | 運用テスト | live-like data flow, no broker side effect |
| paper | 配管とブローカー検証 | order lifecycle fidelity |
| micro_live | 小額本番 | risk control, operator clarity |
| live | 本番 | safety, audit, bounded changes |

## 2.6 SLO / SLA の考え方

### ingest
- realtime watcher heartbeat 欠落は 60 秒以内に検知
- scheduled source miss は release window で検知
- dedupe / event extraction backlog は mode と source tier に応じて上限を持つ

### operator
- prompt task 作成から表示まで数秒以内
- schema validation は貼り付け直後に即応
- decision dossier はインタラクティブに閲覧可能

### execution
- policy decision 後の order routing は deterministic
- same input in replay/shadow should produce same decision
- live では kill switch と mode lock が確実に効く

## 2.7 失敗クラス

### Class A: trading safety
- live mode misfire
- wrong instrument routing
- missing kill switch
- decision/runbook confusion

### Class B: model integrity
- wrong evidence set
- stale market profile
- schema mismatch
- invalid prompt response accepted

### Class C: data pipeline
- watcher dead
- ingest lag
- dedupe explosion
- source parser drift

### Class D: observability / audit
- missing trace_id
- missing prompt version
- missing order linkage
- overwritten ledger

## 2.8 安全策

- mode badge always visible
- live change requires dual confirmation
- policy packs versioned
- prompt responses schema-gated
- outbox + immutable ledgers
- role-separated approvals
- source candidate never goes directly to production

## 2.9 将来市場追加時の NFR

市場が増えると、次が壊れやすい。

- time zone handling
- session templates
- language priority
- calendar conflicts
- benchmark mapping
- regulatory source handling

したがって、市場追加時は NFR の一部として **profile completeness review** を義務化する。
