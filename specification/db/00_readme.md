# DB Package

- `01_core_schema.sql`: v1 の主テーブルと基本ビュー
- `02_extension_schema.sql`: registry / plugin / contract versioning / feature flag 等の拡張テーブル
- `03_views_materialized_views.sql`: dossier / overlay / reliability 向けビュー
- `04_partitioning_retention.sql`: 時系列 ledger の partition / retention 方針
- `05_seed_reference_data.sql`: seed 例 (roles, execution modes, reason codes, event types)

注意:
- `01_core_schema.sql` は core DDL の基礎であり、append-oriented ledger の前提を含む
- 実運用では migration tool (Flyway / Liquibase / Alembic 等) へ分割して投入すること
