# Event Intelligence OS — Status

## v1 Safety Hardening Complete

**Last Updated**: 2026-04-07

## Phase Progress

| Phase | Status |
|-------|--------|
| Phase 0-5: Feature Implementation | **Complete** |
| Fix 1: ORM/SQL Alignment | **Complete** |
| Fix 2: Execution Mode 3-Layer Guard | **Complete** |
| Fix 3: Transactional Outbox | **Complete** |
| Fix 4: trace_id Propagation | **Complete** |
| Fix 5: JWT Auth + RBAC | **Complete** |
| Fix 6: Scoped Kill Switches | **Complete** |
| Fix 7: Safety Tests | **Complete** |

## Final Metrics

| カテゴリ | 数量 |
|---------|------|
| DB テーブル | 54 (7 schemas) |
| SQLAlchemy ORM モデル | 54 |
| API ルート | 59 |
| テスト | 158 |
| サービス | 7 |
| アダプター | 4 (Worker/Broker x ABC/Mock) |
| コミット | 10 |

## v1 Safety Architecture

### Execution Mode (Fail-Closed, 3層)
- **Layer 1**: ExecutionMode enum rejects replay/shadow at service level
- **Layer 2**: Broker adapter registry enforces mode→adapter mapping
- **Layer 3**: Live requires arming with TTL + credentials

### Authentication (JWT + RBAC)
- Roles: viewer < operator < trader < admin
- Capabilities: can_live_trade, can_arm_live, can_kill_switch, can_manage_sources
- Kill switch endpoints: require CAN_KILL_SWITCH
- Extension management: require ADMIN role

### Transactional Outbox
- All critical state transitions emit outbox row in same transaction
- Events: raw_document.created, forecast.created, decision.created, order.submitted, prompt_task.created
- Carries trace_id, correlation_id, idempotency_key

### Trace Propagation
- TraceContext with trace_id + correlation_id + causation_id
- TraceMiddleware on every HTTP request
- All outbox events carry trace automatically

### Kill Switch (5 Scopes)
- TRADE_HALT_GLOBAL: Block new orders
- REDUCE_ONLY_GLOBAL: Block buys, allow sells
- DECISION_HALT: Force no_trade decisions
- SOURCE_INGEST_PAUSE: Per-source ingest block
- FULL_FREEZE: Halt decisions + orders
