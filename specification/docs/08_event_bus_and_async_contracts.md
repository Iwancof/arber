# 08. Event Bus and Async Contracts

## 8.1 なぜ必要か

watchers, extractors, scorers, workflows, UI notifications は時間的に疎結合である。  
同期 API だけだと、再試行と観測がつらい。  
そこで、内部イベントを定義し、outbox から publish する。

## 8.2 v1 方針

v1 ではシンプルにしてよい。

- DB outbox table
- background publisher
- internal topic abstraction
- consumer offsets in app tables

将来 Kafka/NATS/SQS 等へ移しても contract を変えない。

## 8.3 Event Envelope

すべての内部イベントは共通 envelope で包む。

- event_id
- event_name
- event_version
- emitted_at
- producer
- trace_id
- idempotency_key
- partition_key
- payload_schema_name
- payload_schema_version
- payload

## 8.4 Topic 例

- `documents.ingested`
- `documents.deduped`
- `events.extracted`
- `events.verified`
- `forecasts.created`
- `decisions.created`
- `prompt_tasks.created`
- `prompt_responses.accepted`
- `orders.submitted`
- `orders.updated`
- `outcomes.built`
- `postmortems.created`
- `source_candidates.proposed`
- `source_candidates.promoted`

## 8.5 Idempotency

consumer は event_id または idempotency_key ベースで重複除去する。  
少なくとも次では必須。

- document ingest
- event extract
- order submit
- outcome build
- prompt response accept

## 8.6 Delivery Semantics

v1 では **at-least-once** を前提とする。  
exactly-once を夢見て複雑化しない。  
その代わり、consumer 側で idempotent 処理にする。

## 8.7 Ordering

全体順序は保証しない。  
ただし、同一 aggregate では局所順序を守りたい。  
そのため `partition_key` に次を使う。

- document_id
- event_id
- forecast_id
- decision_id
- order_id
- source_candidate_id

## 8.8 Retry / DLQ

### Retry
- transient failures は exponential backoff
- max retry count を持つ

### Dead-letter
- schema invalid
- unknown event type
- impossible state transition
- missing required linkage

DLQ に落ちた payload は operator review 可能にする。

## 8.9 Contract Tests

各 consumer は次を持つ。
- envelope parse test
- schema validation test
- idempotency test
- out-of-order tolerance test

## 8.10 Schema Evolution

- additive fields は許容
- breaking changes は new event_version
- consumers は minimum supported versions を宣言
- outbox publisher は schema registry を参照

## 8.11 Workflow との関係

workflow engine は event bus の代わりではない。  
使い分け:
- **workflow**: long-running orchestration, waiting, compensation
- **event bus**: broadcast, decoupling, fan-out

例:
- prompt task created -> event bus
- prompt task waiting/timeout -> workflow
