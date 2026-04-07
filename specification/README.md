# Event Intelligence OS — Detailed Design Pack v2 (Extensible Edition)

本パックは、`Developer_Handoff_Event_Intelligence_OS_v2` および前回の detailed design pack を発展させた **拡張性重視版** である。  
目的は次の 3 つである。

1. **今すぐ作れる粒度**まで詳細を落とすこと  
2. **将来の市場・ニュースソース・LLM・ブローカー・UI の差し替え余地**を明文化すること  
3. 開発者が **「どこを固定し、どこを抽象化し、どこを後回しにしてよいか」** を迷わない状態にすること

## 本パックの位置づけ

- **上位文書**: `Developer_Handoff_Event_Intelligence_OS_v2`
- **本パック**: 実装詳細、拡張点、データ契約、DB、API、Grafana plugin、運用設計
- **想定読者**: Tech Lead / Backend / Frontend / Grafana Plugin / Data / ML / SRE / QA / Product Owner

## この版で増やしたもの

前版に対し、以下を重点的に追加した。

- **拡張ポイント設計**  
  - market profile / source bundle / worker adapter / broker adapter / policy pack / panel plugin / app plugin
- **市場非依存化の方針**
  - 米国株以外も入れられるように market profile を強化
  - ニュースソース取得を publisher 固定ではなく source registry + endpoint + adapter で表現
- **Grafana-first UI の詳細**
  - 標準ダッシュボード + app plugin + panel plugin の責務分離
  - 価格グラフへの予測帯、イベント、プロンプト状態、判断状態のオーバーレイ
- **DB と契約の拡張性**
  - schema registry, plugin registry, feature flags, contract versioning, outbox/event envelope
- **運用と移行**
  - replay → shadow → paper → micro-live → live
  - source candidate lifecycle
  - schema migration と backward compatibility

## 読み順

### まず読む
1. `docs/00_pack_overview_and_glossary.md`
2. `docs/01_design_principles_and_extension_strategy.md`
3. `docs/02_system_context_and_nfr.md`
4. `docs/03_service_architecture_and_boundaries.md`
5. `docs/04_workflows_core_and_failure_paths.md`

### その後、担当別に読む
- **DB/Backend**
  - `docs/05_database_design_core.md`
  - `docs/06_database_design_extension_patterns.md`
  - `docs/16_schema_versioning_and_migrations.md`
  - `db/*`
- **API/Integration**
  - `docs/07_api_design_operator_control_machine.md`
  - `docs/08_event_bus_and_async_contracts.md`
  - `api/openapi.yaml`
  - `schemas/*`
- **UI/Grafana**
  - `docs/09_ui_design_grafana_shell_and_plugins.md`
  - `docs/10_ui_component_specs_and_interactions.md`
- **ML/LLM**
  - `docs/12_llm_workers_manual_bridge_and_reasoning_trace.md`
  - `docs/20_research_experimentation_and_model_eval.md`
- **Markets / Sources / Broker**
  - `docs/11_source_registry_market_profiles_and_adapters.md`
  - `docs/13_execution_modes_and_broker_abstraction.md`
- **SRE / Security / Ops**
  - `docs/14_observability_security_and_operability.md`
  - `docs/18_data_governance_retention_and_lineage.md`
- **PM / Delivery**
  - `docs/19_delivery_plan_and_backlog.md`
  - `docs/21_architecture_decision_log.md`
  - `adrs/*`

## ファイル一覧

### docs/
- `00_pack_overview_and_glossary.md`
- `01_design_principles_and_extension_strategy.md`
- `02_system_context_and_nfr.md`
- `03_service_architecture_and_boundaries.md`
- `04_workflows_core_and_failure_paths.md`
- `05_database_design_core.md`
- `06_database_design_extension_patterns.md`
- `07_api_design_operator_control_machine.md`
- `08_event_bus_and_async_contracts.md`
- `09_ui_design_grafana_shell_and_plugins.md`
- `10_ui_component_specs_and_interactions.md`
- `11_source_registry_market_profiles_and_adapters.md`
- `12_llm_workers_manual_bridge_and_reasoning_trace.md`
- `13_execution_modes_and_broker_abstraction.md`
- `14_observability_security_and_operability.md`
- `15_testing_simulation_and_validation.md`
- `16_schema_versioning_and_migrations.md`
- `17_plugin_sdk_and_extension_points.md`
- `18_data_governance_retention_and_lineage.md`
- `19_delivery_plan_and_backlog.md`
- `20_research_experimentation_and_model_eval.md`
- `21_architecture_decision_log.md`

### db/
- `00_readme.md`
- `01_core_schema.sql`
- `02_extension_schema.sql`
- `03_views_materialized_views.sql`
- `04_partitioning_retention.sql`
- `05_seed_reference_data.sql`

### api/
- `openapi.yaml`

### schemas/
- `event_record.schema.json`
- `forecast.schema.json`
- `reasoning_trace.schema.json`
- `decision.schema.json`
- `prompt_task.schema.json`
- `prompt_response.schema.json`
- `market_profile.schema.json`
- `source_registry.schema.json`
- `source_bundle.schema.json`
- `event_envelope.schema.json`
- `worker_task.schema.json`
- `worker_result.schema.json`
- `plugin_manifest.schema.json`
- `migration_manifest.schema.json`

### adrs/
- `ADR-001-market-profile-first.md`
- `ADR-002-grafana-shell-with-custom-plugins.md`
- `ADR-003-ledger-separation.md`
- `ADR-004-worker-adapter-contract.md`
- `ADR-005-contract-versioning-and-outbox.md`

## このパックの設計原則

1. **market-specific logic を profile に閉じ込める**
2. **source-specific logic を adapter と registry に閉じ込める**
3. **LLM provider 固有差分を adapter に閉じ込める**
4. **UI は Grafana shell + custom plugin として設計する**
5. **予測・判断・発注・結果・反省を別 ledger で持つ**
6. **すべての重要な構造化データに schema version を持たせる**
7. **v1 は modular monolith、将来は module-by-module に分離可能にする**
8. **今は作らないが将来差し替える場所**を先に明示する

## 重要な注意

- 本パックは **拡張性の余地**を明示するが、v1 で全部を実装することを意味しない。
- **抽象化を導入する場所**と **具体実装で始める場所** を分けること。
- 開発チームは `docs/19_delivery_plan_and_backlog.md` のフェーズと `docs/21_architecture_decision_log.md` を基準にスコープ管理すること。
