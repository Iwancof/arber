@AGENTS.md

# CLAUDE.md

Claude Code project instructions for **Event Intelligence OS**.

## Why this file exists
Use this file for project-specific Claude Code behavior. Keep this file concise. If it grows too large, move topic-specific instructions into `.claude/rules/` or imported files.

## Primary role for Claude Code in this repo
Claude Code is the **main implementation agent**.
Expected responsibilities:
- understand the repository and propose implementation plans,
- scaffold modules and interfaces,
- implement features,
- add tests,
- update schemas and docs,
- keep architecture aligned with the design pack,
- hand off targeted review and adversarial checks to Codex when useful.

Claude Code is **not** the authority to change core architectural direction without documenting it.

## Working style
- Start by summarizing the relevant design docs for the task.
- For work estimated above a small patch, produce a brief implementation plan before editing.
- Prefer incremental commits/patches over giant rewrites.
- Use read-only exploration first, then targeted edits, then verification.
- Run relevant tests after changes.
- Explain any unrun tests explicitly.

## Architecture source of truth
Treat the design pack as normative unless the user explicitly overrides it.
Highest-priority design themes:
- extensibility over hard-coded shortcuts,
- contract-first changes,
- Grafana shell + custom plugins,
- registry/adapter patterns for markets, sources, LLMs, brokers, and UI plugins,
- replay/shadow/paper/live progression,
- typed reasoning traces instead of opaque freeform chain-of-thought storage.

## Required reading for common tasks
### Backend / DB
Read:
- `docs/05_database_design_core.md`
- `docs/06_database_design_extension_patterns.md`
- `docs/16_schema_versioning_and_migrations.md`
- `db/*.sql`

### API / contracts
Read:
- `api/openapi.yaml`
- `schemas/*.json`
- `docs/07_*` and `docs/08_*` if present

### UI / Grafana
Read:
- `docs/09_ui_design_grafana_shell_and_plugins.md`
- `docs/10_ui_component_specs_and_interactions.md`
- relevant plugin manifests or component docs

### LLM / worker behavior
Read:
- `docs/12_llm_workers_manual_bridge_and_reasoning_trace.md`
- worker adapter interfaces

### Markets / sources / adapters
Read:
- `docs/11_source_registry_market_profiles_and_adapters.md`
- market profile schemas / seed data

## How to use Claude Code features here
- Use **subagents** for exploration, comparison, and parallel investigation when tasks span multiple subsystems.
- Use **MCP tools** when the repo provides them for DB inspection, Grafana interaction, API validation, or issue tracking.
- If repetitive workflows emerge, move them into `.claude/skills/` instead of bloating this file.
- If a rule only applies to a directory, prefer `.claude/rules/` or nested CLAUDE files over adding global noise here.

## Implementation rules
- Do not collapse multiple ledgers into one “simpler” table.
- Do not let provider-specific payloads leak across adapter boundaries.
- Do not implement UI-only state as hidden backend truth.
- Do not store raw hidden reasoning as a primary object; store structured reasoning traces and evidence links.
- Prefer explicit enums, versioned payloads, and additive schema evolution.
- Migrations must be forward-applicable and documented.

## Definition of done for non-trivial work
A task is not done unless most of the following are addressed:
- code implemented
- tests added or updated
- DB migration included if needed
- contracts/schemas updated if needed
- docs updated
- observability hooks or metrics considered
- manual verification notes written for UI / Grafana changes

## How to collaborate with Codex
Use Codex primarily for:
- adversarial review,
- test gap discovery,
- contract drift checks,
- regression hunting,
- focused bug-fix follow-up after your implementation.

When handing off to Codex, provide:
- changed files,
- intended behavior,
- relevant design docs,
- exact review or test objective.

## Ask for clarification only when truly blocked
If a decision can be made from existing docs, make it.
If multiple valid options exist, choose the one that best preserves extension points and document the choice.

## Local-only preferences
Put personal machine paths, temporary endpoints, or one-off sandbox notes in `CLAUDE.local.md`, not here.

# 追記

Agent Teamsを使って積極的にチームを作成して並列実装しましょう。

また、一定の進捗があったときは Discord Webhook https://discord.com/api/webhooks/1490946257269821482/o0tN8v3KE7NDJXVwSLTxvLV6at-ucrzyHAwmZgy14-ozdZsd6BmOMFBQobmCFBfCxHa- に通知を飛ばしてください。

開発には git を用い、細かくcommitしてください。

なにか足りないツールやインストールしたいパッケージがあった場合、それをユーザに通知し、別の方法で無理に解決しようとしないでください。

進捗を STATUS.md で管理し、それを全体で共有していく方針で開発を進めてください。
