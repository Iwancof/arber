# 22. Claude Code Front-End Integration

## 1. Why Claude Code

We are intentionally using Claude Code as the operator-facing chat surface rather than building a bespoke chat UI first.

This works because Claude Code supports:
- persistent project instructions via `CLAUDE.md`;
- skills that create slash-command style workflows;
- hooks that can call shell commands, HTTP endpoints, or prompt hooks;
- plugins that can package skills, agents, hooks, and MCP servers.

## 2. Front-end model

Treat Claude Code as a **governed operator console**:
- the conversation happens in Claude Code;
- state comes from MCP-backed query tools;
- actions are routed through MCP-backed control tools or HTTP hooks;
- repo edits use Claude Code's normal code tools, but only in implementation mode.

## 3. Plugin layout suggestion

```text
.claude/
  CLAUDE.md
  rules/
  plugins/
    event-os-copilot/
      skills/
        ops-chat/SKILL.md
        ops-apply/SKILL.md
        ops-implement/SKILL.md
      agents/
        ops-auditor.md
      hooks/
        pretool-audit.json
        posttool-log.json
      mcp/
        read-server.json
        control-server.json
```

## 4. Skills

### `/ops-chat`
Use when the user wants to understand current status.
Default read-only.

### `/ops-apply`
Use when the user wants to convert a conversational instruction into an explicit proposal or operation.

### `/ops-implement`
Use when the user explicitly asks to modify the repository or implementation.

## 5. Agents

### `ops-auditor`
A specialized subagent that:
- challenges unsupported claims;
- checks freshness;
- verifies provenance;
- reviews proposed mutations before execution.

## 6. Hooks

Hooks should be used for deterministic controls.

### Recommended uses
- log every tool/action boundary to the audit API;
- block write tools when session mode is observe/advice only;
- require confirmation banner before dangerous tools;
- auto-attach session metadata and trace ids.

## 7. MCP split

### Read MCP Server
Read-only tools:
- get_global_status
- get_symbol_dossier
- get_inquiry_case
- list_recent_changes
- get_decision_dossier
- search_capsules

### Control MCP Server
Controlled write tools:
- create_note
- create_inquiry
- snooze_inquiry
- approve_proposal
- reject_proposal
- pause_source
- resume_source
- update_watchlist

### Admin / Implementation MCP Server
Expose only when explicitly allowed:
- request_patch_plan
- create_repo_task
- register_source_candidate
- arm_live
- set_threshold_candidate

## 8. Session modes in Claude Code

The chat session should carry a visible mode header:
- OBSERVE
- ADVISE
- OPERATE
- IMPLEMENT

Prompt files and hooks must respect the mode.

## 9. UX expectations

Even though Claude Code is the frontend, the user should experience:
- a live "current state" assistant;
- a question inbox / inquiry tray via commands;
- explainability with provenance;
- proposal previews before mutation;
- explicit mode switching for high-risk operations.

## 10. Minimal required commands

At a minimum the operator should be able to do:

- `/ops-chat what changed in the last 30 minutes?`
- `/ops-chat why are we bearish on TSLA?`
- `/ops-chat show me the open inquiries`
- `/ops-apply snooze the LLY FDA inquiry for 2 hours`
- `/ops-apply pause that source and tell me why`
- `/ops-implement tighten inquiry deduping around FDA headlines`

## 11. Logging and audit

Claude Code conversations that produce proposals or executions must be logged into:
- chat_session
- chat_message
- proposal / execution ledgers
- outbox
- trace correlation fields

## 12. v1 shipping recommendation

Ship:
- read MCP
- control MCP for low-risk actions
- `/ops-chat` and `/ops-apply`
- hooks for audit + permission fences

Do not ship:
- unrestricted repo mutation
- live trading control from chat by default
- unreviewed plugin marketplace dependencies
