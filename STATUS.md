# Event Intelligence OS — Status

## System State: Production (Paper Mode)

**Last Updated**: 2026-04-07

## Running Services

| Service | systemd Unit | Port | Status |
|---------|-------------|------|--------|
| PostgreSQL + Redis + Grafana | `event-os-infra` | 50002/6379/50001 | Running |
| FastAPI API | `event-os-api` | 50000 | Running |
| Pipeline Worker | `event-os-pipeline` | - | Running (5min interval) |

## Pipeline

自動実行中: Alpaca News → Claude Opus 4.6 (event_extract + single_name_forecast) → Policy Engine → Decision

- **LLM**: Claude Opus 4.6 (`claude-opus-4-6`)
- **News Source**: Alpaca News (Benzinga)
- **Interval**: 5分
- **Symbols**: AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, JPM, V, UNH
- **Market**: US_EQUITY

## Architecture

| Category | Count |
|----------|-------|
| DB Tables | 71 (8 schemas) |
| API Routes | 88 |
| Unit Tests | 158 |
| Grafana Dashboards | 7 |
| Services | 7 + ops_chat |
| Adapters | 4 (Worker/Broker × ABC/Mock) + Alpaca + SEC |

## Key URLs

- **API**: http://localhost:50000
- **API Docs**: http://localhost:50000/docs
- **Inquiry UI**: http://localhost:50000/v1/ui/inquiry
- **Grafana**: http://localhost:50001 (admin/admin)

## DB Schemas

| Schema | Purpose | Tables |
|--------|---------|--------|
| core | Markets, instruments, users, extensions | 17 |
| sources | Source registry, watch plans | 9 |
| content | Documents, events | 6 |
| forecasting | Forecasts, decisions, prompts | 10 |
| execution | Orders, fills, positions | 3 |
| feedback | Outcomes, postmortems, reliability | 4 |
| ops | Audit, kill switch, config, outbox | 6 |
| human_ops | Inquiry cases, tasks, responses | 8 |
| ops_chat | Chat sessions, capsules, proposals | 9 |

## Safety Architecture

- **Execution Mode**: 3-layer fail-closed (service → adapter registry → live arming)
- **Auth**: JWT + RBAC (viewer/operator/trader/admin), disabled in dev
- **Kill Switch**: 5 scopes (trade_halt, reduce_only, decision_halt, source_pause, full_freeze)
- **Outbox**: Transactional outbox on all critical paths
- **Trace**: trace_id propagation via middleware

## Completed Implementation Phases

1. Phase 0: Skeleton (DB, API, Grafana)
2. Phase 1: Ingest (ORM 54 tables, source/market/event API)
3. Phase 2: Forecast (Worker adapter, forecast/decision pipeline)
4. Phase 3: Manual Bridge + Replay (prompt lifecycle, replay engine, postmortem)
5. Phase 4: Paper+Live (broker adapter, order lifecycle, kill switch)
6. Phase 5: Extensibility (plugin/schema/flag/contract registries)
7. Safety Hardening (ORM alignment, mode guards, outbox, trace, auth, kill switch scope)
8. Real Pipeline (Anthropic worker, Alpaca adapters, background worker)
9. Human Inquiry Orchestration (case/task lifecycle, 8 tables, 16 API endpoints)
10. Ops Chat Copilot (context capsules, intent/proposal, 9 tables, 11 API endpoints)
11. Visualization (7 Grafana dashboards, Inquiry answer web UI)
12. Claude Code Skills (/ops-chat, /ops-apply)

## Pending / Known Issues

- Prompt refinement: waiting for design team response
- SEC EDGAR adapter: built but not connected to pipeline
- Integration tests: unit tests only, no full E2E test suite
- Alembic migrations: using docker-entrypoint SQL, no versioned migrations
