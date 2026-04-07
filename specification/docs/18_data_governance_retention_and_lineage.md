# 18. Data Governance, Retention, and Lineage

## 18.1 目的

再現性と監査性を守りつつ、データ量の膨張を制御する。

## 18.2 分類

- raw external data
- structured events
- model outputs
- operator inputs
- execution records
- system telemetry

## 18.3 Retention Policy

### 長期保存
- raw_document metadata
- event_ledger
- forecast_ledger
- decision_ledger
- order_ledger
- outcome_ledger
- postmortem_ledger
- audit_log

### 短期 or tiered
- full raw payload blobs
- prompt pack rendered artifacts
- transient workflow payloads
- noisy parser debug logs

## 18.4 Lineage

最低でも以下の lineage を辿れるようにする。

`raw_document -> event -> retrieval_set -> forecast -> decision -> order -> outcome -> postmortem`

manual bridge があれば、
`prompt_task -> prompt_response -> decision rerun`
も辿れること。

## 18.5 Provenance Columns

- created_by_component
- created_by_version
- source_id
- schema_version
- prompt_version
- worker_adapter_version
- plugin_code
- actor_id

## 18.6 Redaction / Privacy

本システムは通常 PII を強く扱わないが、
- operator notes
- manual pasted text
- auth metadata
などに機微が混じる可能性がある。  
raw response retention と access scope は明示する。

## 18.7 Legal / Compliance Flags

source registry に legal notes を持たせ、
- scraping allowed?
- redistribution allowed?
- retention limits?
を明示する。

## 18.8 Deletion Strategy

ledger は hard delete しない。  
必要なら tombstone / visibility restriction / external blob purge を使う。

## 18.9 Export and Reproducibility

replay のため、次を export 可能にする。
- raw documents by time range
- event ledger by market range
- forecast and decision snapshots
- prompt versions and plugin manifests
- market profile snapshot
- source bundle snapshot
