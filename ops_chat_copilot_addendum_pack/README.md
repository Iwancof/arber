# Operations Chat Copilot Addendum

This addendum extends Event Intelligence OS with an operator-facing chat copilot built around Claude Code as the interactive front end.

## Goals
- Let the user ask, in chat form, what the system currently knows.
- Let the assistant answer from structured system state rather than from raw hidden reasoning.
- Let approved user instructions feed back into the system safely.
- Let Claude Code serve as the operator UX via skills, hooks, agents, and MCP-backed tools.
- Keep the system running even if the user never answers pending questions.

## Included artifacts
- `docs/19_ops_chat_copilot_architecture.md`
- `docs/20_ops_context_assembly.md`
- `docs/21_ops_chat_response_application.md`
- `docs/22_claude_code_frontend_integration.md`
- `db/04_ops_chat_extension.sql`
- `api/openapi_ops_chat.yaml`
- `prompts/ops_chat_system_prompt.md`
- `prompts/context_capsule_builder.md`
- `prompts/intent_extractor.md`
- `prompts/action_proposer.md`
- `prompts/action_reflector.md`
- Claude Code skill prompts under `prompts/claude_plugin/skills/`

## Scope
This addendum is intentionally compatible with the existing:
- ledger model (`event`, `forecast`, `decision`, `order`, `outcome`, `postmortem`)
- Human Inquiry Orchestration subsystem
- Grafana-first UI and plugin shell
- Worker / broker / source registries

## Design headline
Treat the chat copilot as a **read-mostly operational layer with controlled write-back**:
1. Assemble structured context capsules from system ledgers.
2. Answer chat questions from those capsules plus on-demand retrieval.
3. Convert approved user instructions into explicit proposals and commands.
4. Apply commands through existing APIs and record every effect in ledgers and outbox.
