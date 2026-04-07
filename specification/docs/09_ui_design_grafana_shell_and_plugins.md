# 09. UI Design — Grafana Shell and Plugins

## 9.1 基本方針

UI は **Grafana-first** とする。  
ただし、標準ダッシュボードだけではなく、

- standard dashboards
- app plugin custom pages
- panel plugin custom visualizations
- data links / trace correlations

を組み合わせて、**Grafana 上の自前業務アプリ**として構築する。

## 9.2 なぜ独立Webアプリではなく Grafana shell か

### Grafana を使う利点
- metrics/logs/traces と業務データを近くに置ける
- alerting と navigation がある
- datasource provisioning しやすい
- operator が同じ shell 上で観測と判断を行える
- candlestick, timeseries, state timeline, annotations をそのまま活用できる

### ただし
Prompt Console や Source Candidate Review は標準パネルでは足りない。  
そのため app plugin custom pages を使う。

## 9.3 画面の責務分離

### Standard dashboards
- Market Overlay Dashboard
- Watcher Health Dashboard
- Model Quality Dashboard
- Paper vs Live Drift Dashboard

### App plugin pages
- Event Inbox
- Decision Dossier
- Prompt Console
- Source Registry
- Source Candidate Review
- Postmortem Explorer
- Plugin Registry / Feature Flags

### Panel plugins
- Forecast Band Overlay Panel
- Decision Timeline Panel
- Prompt Lifecycle Ribbon
- Reliability Heatmap
- Source Coverage Map

## 9.4 Navigation

左ナビの推奨構成:
- Overview
- Markets
- Inbox
- Dossiers
- Prompts
- Sources
- Replay
- Postmortems
- Operations
- Admin

## 9.5 権限と UI

- viewer は dashboards + read-only plugin pages
- operator は prompt / source candidate / replay actions
- trader_admin は live / broker / kill switch
- platform_admin は plugin registry, source registry, schema registry

UI 要素は role に応じて非表示ではなく disabled + reason 表示が望ましい。

## 9.6 Plugin Architecture

### App plugin
- navigation
- page routing
- action buttons
- backend proxy / query facade
- saved filters
- per-page permission checks

### Panel plugin
- custom rendering
- overlay config
- click-to-dossier
- annotation clustering
- forecast band shading
- position / order markers

## 9.7 Dossier-first 設計

本システムの中心 UI は Dossier である。  
1 decision / 1 event / 1 symbol を end-to-end で理解できることを重視する。  
Dossier には必ず次が含まれる。

- market context
- price + overlay
- source evidence summary
- reasoning trace summary
- manual prompt state
- decision summary
- order summary
- outcome / historical reliability

## 9.8 UI に出す reasoning の扱い

生の長文 chain-of-thought は出さない。  
表示するのは次の structured reasoning trace。

- hypotheses
- selected_hypothesis
- counterarguments
- risk_flags
- evidence_refs
- confidence_before/after
- trace version

## 9.9 UI State Design

### statuses
- created
- awaiting_manual
- manual_submitted
- accepted
- proposed
- no_trade
- executed
- expired
- errored

### visual treatment
- live influence: red/orange
- manual pending: amber
- no-trade: gray
- replay/shadow: blue
- paper: purple
- live: red badge

## 9.10 Future-ready UI

将来追加できるようにするもの:

- per-market layouts
- additional panel plugins
- custom dossier tabs
- experiment views
- source-specific admin pages

それでも v1 では **ナビゲーションの土台**だけ用意し、実際のページ数は絞る。
