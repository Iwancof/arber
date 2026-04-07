# code_review.md

Detailed review rubric for Codex and humans reviewing **Event Intelligence OS**.

## Review goal
Find correctness, safety, migration, contract, extensibility, and operability issues before style nits.

## Severity scale
- **P0**: data loss, order-routing safety issue, broken kill switch, obvious security issue, destructive migration risk
- **P1**: contract breakage, incorrect execution-mode behavior, missing compatibility handling, silent observability gap on critical flow
- **P2**: significant test gap, brittle plugin coupling, poor adapter isolation, likely performance or maintainability issue
- **P3**: style / naming / minor docs issues

## What to review first
1. Contract changes (`OpenAPI`, JSON Schema, typed payloads)
2. DB migrations and backward compatibility
3. Execution path (`decision -> order -> outcome`)
4. Source registry / market profile / adapter boundaries
5. Grafana plugin boundaries and data flow
6. LLM worker and reasoning trace contracts
7. Tests and observability

## Critical invariants to protect
- `event`, `forecast`, `decision`, `order`, `outcome`, and `postmortem` remain separate ledgers
- execution modes remain explicit and non-confusable
- market/source/provider-specific logic stays behind adapters or profiles
- UI state is not treated as audit truth
- schema versioning remains explicit for externally meaningful structures
- manual expert bridge does not become mandatory for fast-path execution

## Review checklist
### A. Contracts
- Are any fields renamed, removed, or repurposed without versioning?
- Are enums widened safely?
- Are nullable / optional semantics clear?
- Are consumers updated consistently?

### B. Database
- Are migrations reversible or at least carefully staged?
- Are indexes and uniqueness constraints still valid?
- Is append-only behavior preserved where expected?
- Are retention / partitioning assumptions still correct?

### C. Execution safety
- Could this change accidentally submit live orders from a non-live mode?
- Are kill-switches still reachable and respected?
- Are paper/shadow/live paths cleanly separated?
- Are broker adapter assumptions hidden anywhere outside adapters?

### D. Extensibility
- Did the change hard-code a market, broker, provider, or source?
- Did it bypass registry-driven discovery?
- Did it create new coupling that will make multi-market support harder?

### E. UI / Grafana
- Is the change correctly split between standard dashboards, app plugin pages, and panel plugins?
- Are overlays driven from structured data rather than presentation-specific hacks?
- Is operator workflow auditable?

### F. LLM / reasoning trace
- Are structured reasoning traces preserved?
- Is raw hidden reasoning avoided as a durable primary artifact?
- Are evidence references explicit and reviewable?
- Are worker/provider-specific payloads normalized before storage?

### G. Testing
- Are unit tests present for logic-heavy changes?
- Are contract tests present for schema/API changes?
- Are migration checks present for DB changes?
- Are integration or replay-mode checks present for execution changes?

### H. Observability
- Are new long-running tasks measurable?
- Are failures emitted with enough context?
- Can operators understand what broke without re-reading code?

## Recommended Codex review prompt
Review this change against `AGENTS.md` and `code_review.md`.
Focus on P0/P1 findings first.
Check contract safety, migration safety, execution-mode correctness, adapter boundary violations, missing tests, and observability regressions.
Do not spend time on style unless it affects correctness or maintainability.
