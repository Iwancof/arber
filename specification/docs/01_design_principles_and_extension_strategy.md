# 01. Design Principles and Extension Strategy

## 1.1 背景

本システムは、ニュースや開示をもとに市場を観測し、予測・判断・実行・反省を行う。  
ただし、最初から巨大なプラットフォームを作ると運用が破綻しやすい。  
一方で、対象市場・ソース・LLM・ブローカーは将来必ず増える。  
したがって **「最初は小さく作るが、差し替え箇所は最初に決める」** のが方針である。

## 1.2 主要原則

### 原則A: Config before code
市場追加、ソース追加、worker 追加、policy 切替、UI overlay 追加は、できるだけ **設定データ**で表現する。  
if 文や provider 固定の分岐をアプリ全体に散らさない。

### 原則B: Contract before implementation
adapter 間の境界は、実装より先に contract を決める。  
例:
- `WorkerTask / WorkerResult`
- `EventEnvelope`
- `Forecast`
- `Decision`
- `PromptTask / PromptResponse`
- `PluginManifest`

### 原則C: Append-oriented ledgers
予測と判断は履歴を上書きしない。  
過去の verdict や score を消してはいけない。  
修正が必要なら新しい ledger row と補正リンクを作る。

### 原則D: Explicit extension seams
拡張点は「暗黙」ではなく「明示」する。  
例えば次の seam を先に定義する。

- market profile seam
- source adapter seam
- worker adapter seam
- broker adapter seam
- policy pack seam
- dashboard panel seam
- app page seam
- event schema seam
- async event seam

### 原則E: UI shell and workbench separation
監視・分析・操作を 1 枚の巨大画面に詰め込まない。  
Grafana を shell とし、その上に
- dashboard
- custom page
- custom panel
- data links / correlations
を積む。

### 原則F: Human-in-the-loop but not human-on-the-critical-path
人間の判断は強力だが、**秒単位の必須依存**にしない。  
手動LLMや operator approval は fallback 可能な設計にする。

### 原則G: Pragmatic modular monolith first
v1 は modular monolith でよい。  
ただし、将来分離しそうな境界は最初から package / schema / topic で切る。

## 1.3 拡張戦略

### v1 で固定してよいもの
- PostgreSQL を主系ストアにする
- Grafana を UI shell にする
- Replay / Shadow / Paper / Micro-live を作る
- Manual Expert Bridge を operator workflow に置く
- Source registry / market profile / watch plan を使う

### v1 で抽象化しておくべきもの
- market profile
- source adapter
- worker adapter
- broker adapter
- schema versioning
- plugin manifest
- feature flag
- event bus envelope

### v1 で過度に抽象化しなくてよいもの
- scoring model の学習アルゴリズム
- Grafana plugin のテーマシステム
- full multi-tenant authz model
- arbitrary strategy composition DSL
- runtime plugin hot-reload

## 1.4 拡張点の一覧

| 拡張点 | 目的 | v1 実装方針 | 将来の拡張 |
|---|---|---|---|
| market profile | 市場ごとの差異吸収 | DB + config | profile inheritance / policy packs |
| source adapter | ソース取得差異吸収 | adapter_type + adapter impl | marketplace / third-party plugins |
| worker adapter | LLM/API/CLI の差異吸収 | common task/result contract | multiple providers, ensemble |
| broker adapter | broker 差異吸収 | single broker first | multi-broker routing |
| schema registry | payload 進化管理 | table + JSON schema files | compatibility enforcement tooling |
| event bus | module decoupling | outbox + internal topics | Kafka/NATS split |
| plugin SDK | Grafana UI 拡張 | manifest + app/panel contracts | third-party plugins |
| policy pack | 戦略差替え | config-driven rules + versions | pack store / simulation catalog |

## 1.5 拡張性のための禁止事項

- 具体的な市場名でコードを分岐させること
- Alpaca / SEC / Claude / Codex など provider 名を core domain へ埋め込むこと
- reasoning trace を provider 固有 raw text だけで保存すること
- event type をコード内 enum のみで管理し、DB で version を持たないこと
- dashboard に直接 SQL を直書きして business logic を埋めること
- paper と live で別の strategy code path を持つこと

## 1.6 どこに余白を残すか

### 余白を残すべき場所
- contract version
- metadata_json
- source coverage tags
- market profile policy json
- plugin manifest capabilities
- event reason codes
- reliability dimensions

### 余白を残しすぎてはいけない場所
- core keys
- mode state machine
- ledger separation
- authz role names
- prompt response acceptance criteria
- order state transitions

## 1.7 運用に効く拡張性

拡張性は将来の夢ではなく、**日々の運用変更**に効かなければ意味がない。  
本システムでは次がすぐ効く。

- 新しい監視ソースを provisional で追加できる
- source gap の多い領域だけ overlay bundle を追加できる
- 특정 event type だけ manual bridge を強化できる
- 特定市場だけ live を止めて他市場を継続できる
- 予測帯 overlay を panel plugin の追加だけで増やせる
