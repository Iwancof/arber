# 14. Observability, Security, and Operability

## 14.1 Observability Stack

- metrics
- logs
- traces
- audit logs
- operational dashboards
- business dashboards

## 14.2 Trace Strategy

すべての重要な flow に trace_id を通す。

- raw ingest
- extraction
- forecast
- decision
- prompt task
- prompt response
- order routing
- outcome build

Grafana shell から trace/log/metric/decision dossier を相互ジャンプできるようにする。

## 14.3 Metrics

### Pipeline
- ingest lag
- watcher heartbeat age
- parse success rate
- dedupe ratio
- extraction backlog

### Model
- schema valid rate
- confidence distribution
- calibration drift
- brier by event type

### Execution
- order reject rate
- partial fill rate
- paper/live drift
- kill switch activations

### Human-in-loop
- prompt task latency
- acceptance rate
- reformat rate
- expired task count

## 14.4 Logs

構造化ログ必須:
- trace_id
- actor_id
- market_profile
- component
- entity refs
- mode
- severity

## 14.5 Audit

次を audit 対象にする。
- source changes
- prompt accept/reject
- live arm/disarm
- kill switch
- plugin enable/disable
- schema registry changes
- migration apply
- policy pack rollout

## 14.6 Security

### Principle of least privilege
- broker write perms limited
- worker tokens scoped
- plugin backend no direct DB mutate
- secret store mandatory

### Data boundaries
- raw external responses segregated
- manual bridge responses scrubbed
- PII not expected but still classify fields

## 14.7 RBAC

- viewer
- operator
- trader_admin
- platform_admin

role に加えて resource scope を持つ。
例:
- market level
- environment level
- plugin level

## 14.8 Kill Switch Design

種類:
- global
- market
- strategy/policy pack
- source-specific
- broker-specific

発動後は理由・actor・scope・expected recovery path を残す。

## 14.9 Operational Readiness

- runbooks
- dashboard links
- escalation matrix
- backup and restore
- migration rollback plan
- replay-based smoke tests

## 14.10 Plugin Operability

plugin は health endpoint と manifest を持つ。  
壊れた plugin は safely disabled できること。
