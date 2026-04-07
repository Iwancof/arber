# 16. Schema Versioning and Migrations

## 16.1 目的

拡張性を持たせるには、**データ契約の進化**を制御しなければならない。  
この文書では schema registry, payload versions, DB migrations, plugin compatibility を定義する。

## 16.2 対象

- JSON schemas
- event envelopes
- API payloads
- ledger json payloads
- plugin manifests
- worker task/result
- DB schema migrations

## 16.3 Version Taxonomy

- `schema_version`: JSON payload contract version
- `payload_version`: 生成された payload の内部版
- `api_version`: endpoint compatibility
- `db_migration_version`: DB structure changes
- `plugin_api_version`: plugin host contract
- `adapter_version`: source/worker/broker adapter implementation version

## 16.4 Schema Registry

registry に持つべき列:
- schema_name
- semantic_version
- status
- owner
- backward_compatible_from
- forward_compatible_to
- rollout_state
- json_schema_uri
- sample_payload_uri

## 16.5 Change Rules

### Non-breaking
- optional field addition
- new metadata block
- new enum if consumer tolerates unknowns

### Breaking
- required field addition
- field rename
- semantic reinterpretation
- enum removal
- shape changes

breaking は new major version。

## 16.6 Migration Manifest

migration 単位で次を残す。

- migration_id
- target_component
- from_version
- to_version
- breaking flag
- rollout plan
- rollback plan
- data backfill required
- validation query

## 16.7 Dual Read / Dual Write

重要 payload を切り替えるときは、
- old + new で read
- new only write after cutover
- backfill where needed

v1 では高頻度にやりすぎないが、仕組みは持つ。

## 16.8 DB Migration Policy

- SQL migrations are source-controlled
- backward-compatible DB changes first
- destructive changes only after deprecation window
- materialized views refreshed after cutover
- plugin compatibility check before rollout

## 16.9 Contract CI

CI で必ず行う:
- JSON schema validation on samples
- OpenAPI lint
- migration apply on empty DB
- migration apply on previous snapshot
- plugin manifest compatibility test
- worker contract sample test

## 16.10 Event Type Evolution

event_type は registry で管理。  
unknown event type を完全 reject せず、
- provisional type
- review queue
- later registry promotion
の流れを許容する。

## 16.11 Backfill Strategy

backfill を必要とするもの:
- benchmark map changes
- schema interpretation changes
- source bundle reclassification
- reliability dimension changes

backfill job は workflow 化する。
