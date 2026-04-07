# 00. Pack Overview and Glossary

## 0.1 本パックのゴール

本パックは、Event Intelligence OS を **市場観測・LLM支援・判断・発注・反省** まで一貫して扱うソフトウェアとして実装するための詳細設計書群である。  
本システムは単一の「予測AI」ではなく、次の構成要素から成る。

- 監視基盤 (watchers, planners, adapters)
- イベント抽出基盤 (event extractor, verifier, dedupe)
- 記憶基盤 (ledgers, retrieval, semantic stats, reliability store)
- 判断基盤 (forecast, skeptic, baseline, meta scorer, policy engine)
- 実行基盤 (execution modes, broker adapters, risk gates)
- 可視化基盤 (Grafana shell, dashboards, custom pages/panels)
- 人間介入基盤 (Manual Expert Bridge, prompt console, approval flows)
- 反省基盤 (outcome builder, judge, postmortem, source candidate lifecycle)

## 0.2 何を固定し、何を可変にするか

### 固定するもの
- ledger 分離の原則
- structured output / structured reasoning trace の採用
- market profile / source registry / worker adapter / broker adapter という抽象層
- replay → shadow → paper → micro-live → live の移行順
- Grafana-first UI であること
- append-oriented auditability

### 可変にするもの
- 対象市場
- source bundles
- LLM providers / CLI workers / manual bridge の組み合わせ
- ブローカー
- scoring model の中身
- policy pack
- UI plugin の中身
- overlay 表現の粒度
- 監視ソースの追加・削除・昇格

## 0.3 用語集

| 用語 | 意味 |
|---|---|
| market profile | 市場の人格。タイムゾーン、セッション、ベンチマーク、デフォルトソース束などをまとめた定義 |
| source registry | 監視対象ソースの台帳。publisher, endpoint, adapter, trust, coverage を持つ |
| source bundle | 市場やセクターごとに使うソース集合 |
| watch plan | どのソース watcher を今動かすかを決めた計画 |
| event ledger | 抽出済みイベントの append-only 台帳 |
| forecast ledger | 予測の append-only 台帳 |
| decision ledger | スコアリングと policy 判定の結果台帳 |
| order ledger | 注文の台帳 |
| outcome ledger | 事後の実現結果台帳 |
| postmortem ledger | 正誤分析と failure code の台帳 |
| reasoning trace | LLM の生の思考全文ではなく、構造化された仮説・反証・選択の記録 |
| Manual Expert Bridge | 人が Web の高性能 LLM を使い、その出力を構造化してシステムへ返す仕組み |
| baseline engine | LLM に頼らない定量ベースライン予測器 |
| meta scorer | 複数の入力を統合して最終 score を返す決定論 or 軽量ML層 |
| policy pack | score と risk 条件から no-trade / propose / execute を決めるルール束 |
| plugin | Grafana shell 上に追加する app page, panel, overlay, integration |
| contract | JSON schema, API payload, event envelope などの相互接続仕様 |
| outbox | DB commit と event publish の整合性を取るための内部イベント排出テーブル |

## 0.4 対象外

本パックは次を主目的にしない。

- 数学的な alpha 証明
- HFT / co-location / ultra-low-latency execution
- いきなりの multi-tenant SaaS 化
- 全 asset class を v1 で一括実装すること
- LLM の自由作文 UI をそのまま本番意思決定へ使うこと

## 0.5 成功条件

本システムは、次を満たしたら v1 として成功とみなす。

1. 監視 → 予測 → 判断 → 反省 の流れが **同じ ledger 群**で追跡できる  
2. replay / shadow / paper を **同じ strategy code** で回せる  
3. Grafana 上で、価格・予測帯・イベント・判断・プロンプト状態を重ねて見られる  
4. 新しい市場・ニュースソース・LLM worker を **コード全体を書き換えず**追加できる  
5. 本番運用前に paper/live 差分を説明できる程度の observability がある
