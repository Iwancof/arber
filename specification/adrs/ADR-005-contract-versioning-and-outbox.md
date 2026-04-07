# ADR-005: Contract Versioning and Outbox

## Status
Accepted

## Context
schema evolution と内部イベントの整合性を管理したい。

## Decision
schema registry + outbox pattern を採用する。

## Consequences
- migration discipline が必要
- at-least-once / idempotency 前提の consumer 実装が必要
