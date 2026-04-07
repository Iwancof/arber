# AGENTS.md

Repository-wide instructions for coding agents working on **Event Intelligence OS**.

## Purpose
This repository implements the Grafana-first, extensible **Event Intelligence OS** described in the design pack. The goal is not to prototype quickly at any cost; it is to build a system that can evolve across markets, news sources, LLM providers, brokers, and UI plugins without breaking core contracts.

## Read this first
Before making material changes, read in this order if present:
1. `README.md`
2. `Developer_Handoff_Event_Intelligence_OS_v2.md` or `.docx`
3. `event_os_detailed_design_pack_v2_extensible/README.md`
4. `docs/01_design_principles_and_extension_strategy.md`
5. `docs/05_database_design_core.md`
6. `docs/06_database_design_extension_patterns.md`
7. `docs/09_ui_design_grafana_shell_and_plugins.md`
8. `docs/11_source_registry_market_profiles_and_adapters.md`
9. `docs/12_llm_workers_manual_bridge_and_reasoning_trace.md`
10. `docs/16_schema_versioning_and_migrations.md`
11. `api/openapi.yaml`
12. `db/*.sql`

If these paths differ in the actual repo, find the closest equivalent before changing architecture.

## Core invariants
- Preserve **ledger separation**: `event`, `forecast`, `decision`, `order`, `outcome`, `postmortem` stay distinct.
- Preserve **Grafana-first UI**: standard dashboards + app plugin + panel plugin. Do not pivot to a standalone UI unless explicitly requested.
- Preserve **market/source/provider abstraction**: market-specific logic belongs in `market_profile`; source-specific logic belongs in registry + adapter layers; provider-specific logic belongs in worker adapters.
- Keep **LLM reasoning separate from execution**. LLMs may propose or score; deterministic policy and broker layers decide execution.
- Keep **execution modes** distinct: `replay`, `shadow`, `paper`, `micro_live`, `live`.
- Prefer **append-only ledgers** and explicit versioning over in-place mutation.
- All externally consumed structured data must carry a schema version.

## Delivery approach
- Work in small vertical slices.
- Do not redesign the whole system while implementing one feature.
- If you need to change a core architectural invariant, stop and add/update an ADR before coding.
- When unsure, choose the more extensible contract even if the first implementation is simple.

## Required outputs for meaningful changes
For any non-trivial change, update all affected layers:
- implementation code
- tests
- schema / migration files if contracts or DB change
- OpenAPI / JSON Schema if API or payloads change
- docs / ADRs if architecture or workflows change
- observability if new long-running or failure-prone behavior is introduced

## Commands
Prefer these repository-standard commands if present:
- `make fmt`
- `make lint`
- `make typecheck`
- `make test`
- `make test-unit`
- `make test-integration`
- `make test-contract`
- `make test-ui`
- `make db-migrate`
- `make db-verify`
- `make api-validate`
- `make plugin-build`
- `make compose-up`

If they do not exist yet, create them before adding more bespoke commands.

## Testing expectations
- New behavior needs tests or a clear explanation of why tests are not yet possible.
- DB changes need migration tests or at minimum migration verification steps.
- API changes need contract validation.
- Grafana plugin changes need component tests and a manual verification note.
- Execution logic changes must not skip replay/shadow-mode validation.

## Review expectations
Use `code_review.md` as the detailed review rubric. During review, prioritize:
1. contract breakage
2. migration safety
3. execution-mode safety
4. observability gaps
5. hidden coupling that reduces extensibility

## Safety rules
- Never hard-code secrets or credentials.
- Never couple logic to a single market, source, or provider unless the adapter boundary explicitly requires it.
- Do not remove auditability to make code simpler.
- Do not merge “helpful” schema changes without versioning and compatibility notes.
- Do not silently relax risk controls or kill-switch behavior.

## When blocked
If requirements are ambiguous:
- make the smallest reversible change,
- leave clear TODOs only when necessary,
- and document assumptions in code comments or an ADR.

## Future scaling pattern
As directories stabilize, add nested `AGENTS.md` or `AGENTS.override.md` files close to specialized code (for example `backend/`, `db/`, `grafana/`, `workers/`, `infra/`). Keep those local files focused on the directory they govern.
