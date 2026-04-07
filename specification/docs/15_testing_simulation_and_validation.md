# 15. Testing, Simulation, and Validation

## 15.1 方針

本システムでは **予測の良し悪し** と **ソフトが正しく動くこと** を分けて検証する。

## 15.2 テスト層

### Unit
- parser
- schema validation
- scoring rule
- policy rule
- adapter mapping

### Integration
- watcher -> raw_document
- extraction -> event ledger
- forecast -> decision
- prompt task -> response acceptance
- broker adapter -> order ledger

### Contract
- JSON schemas
- event envelope
- OpenAPI examples
- plugin manifest
- worker task/result

### Replay
- historical time-safe replays
- deterministic outputs with fixed seeds where possible
- prompt version snapshot compatibility

### End-to-end
- shadow mode full path
- paper mode full path
- micro-live dry run

## 15.3 Acceptance Criteria

### v1 system
- no orphan ledgers
- no mode confusion in UI
- manual prompt lifecycle works
- overlay panel renders forecast + annotations
- replay reproduces same decision from same inputs

### source candidate
- dry-run metrics available
- promotion requires review
- rollback to disabled works

## 15.4 Model Evaluation

追うべきもの:
- Brier
- calibration
- relative return bucket accuracy
- downside barrier hit quality
- no-trade quality
- decision uplift vs baselines

## 15.5 Paper vs Live Validation

paper success is insufficient。  
必要:
- paper_adjusted vs paper_broker
- shadow vs paper
- micro-live drift dashboard

## 15.6 UI Validation

- panel rendering with dense annotations
- role-based visibility
- live badge unmistakable
- prompt paste / parse UX
- source registry actions

## 15.7 Migration Testing

- forward migration
- rollback feasibility
- old payload read support
- dual schema coexistence
- plugin compatibility checks

## 15.8 Chaos / Failure Tests

- watcher outage
- provider timeout
- schema invalid flood
- broker reject burst
- prompt task expiry storm
- kill switch activation during pending orders
