# 03. Service Architecture and Boundaries

## 3.1 推奨構成

v1 は **modular monolith + durable workflows + plugin shell** を推奨する。  
デプロイ単位を過度に分けず、コード境界と DB schema 境界を先に切る。

```text
ui-shell/
  grafana/
  app-plugins/
  panel-plugins/

platform-api/
  operator-api/
  control-api/
  internal-api/

core-engine/
  watch-planner/
  ingest-gateway/
  extractor/
  verifier/
  retrieval/
  forecast/
  meta-scorer/
  policy/
  execution/

workflows/
  replay/
  prompt-bridge/
  source-onboarding/
  postmortem/

stores/
  postgres/
  redis/
  object-storage/
```

## 3.2 Bounded Context

### Core
市場、銘柄、ユーザー、ロール、feature flags、plugin registry、schema registry。

### Sources
source registry, endpoints, bundles, watch plan, source candidate, adapter run state。

### Content
raw document, dedupe cluster, event ledger, evidence links。

### Forecasting
retrieval sets, reasoning trace, forecast ledger, decision ledger, reliability store。

### Execution
execution modes, broker adapter, order ledger, fills, positions, risk gates。

### Feedback
outcome ledger, postmortem ledger, judge results, source gap statistics。

### Ops
audit log, watcher instance, workflow run, alert state, kill switch。

## 3.3 モジュール境界の原則

- Core は provider 名を知らない
- Sources は broker を知らない
- Execution は raw LLM text を知らない
- UI は business logic を SQL へ埋め込まない
- Plugin は ledger schema を直接 mutate しない
- Worker adapter は domain object ではなく contract object を受け取る

## 3.4 将来分離しやすい順

将来 microservice 化するなら、次の順で切り出しやすい。

1. watch / ingest gateway
2. execution service
3. replay engine
4. source onboarding workflow
5. plugin backend facade

Meta scorer と operator API は当面 monolith 内でよい。

## 3.5 パッケージ構成の例

```text
src/
  core/
  sources/
  content/
  forecasting/
  execution/
  feedback/
  ops/
  contracts/
  plugins/
  workflows/
```

## 3.6 依存関係ルール

- `core` は最下層
- `contracts` は上位が参照する共通層
- `forecasting` は `content` を読むが `execution` を直接更新しない
- `execution` は `decision ledger` を読むが `forecast` を再計算しない
- `feedback` は全 ledger を参照するが、過去 ledger を更新しない
- `plugins` は API facade 経由でのみ state change を行う

## 3.7 Workflow Engine の置き場所

長寿命・人手待ち・再試行が絡むものは workflow 管轄にする。

- prompt task lifecycle
- replay job
- source candidate dry-run
- scheduled macro release preparation
- postmortem batch

即時応答が必要な query は workflow に入れない。

## 3.8 Repository 運用

v1 では mono-repo を推奨する。  
理由:
- contract と schema を一緒に version 管理しやすい
- Grafana plugin と backend の同期がしやすい
- migrations と app release の追跡が容易

### 推奨トップレベル
```text
/docs
/db
/api
/schemas
/services
/plugins
/workflows
/infra
/tests
```

## 3.9 セキュリティ境界

- ブローカー書込権限は execution service のみ
- source write / promotion は control plane のみ
- plugin page は operator API のみ叩く
- workflow workers は scoped token
- manual prompt raw response は PII/secret scrub を通す
