# 19. Operations Chat Copilot Architecture

## 1. Purpose

Add an operator-facing chat copilot that can:
- answer questions about what the system currently knows;
- explain which events, forecasts, decisions, orders, inquiries, and plans exist;
- summarize recent changes;
- propose changes back into the operating system;
- optionally, when explicit permission is granted, modify repository/configuration artifacts using Claude Code's normal coding abilities.

The chat copilot is **not** a free-form hidden-reasoning window.  
It is a governed interface over structured operational state.

## 2. Core principles

### 2.1 Facts first
The chat assistant answers from:
- ledgers;
- context capsules;
- inquiry cases;
- source registry state;
- observability summaries;
- approved configuration snapshots.

It must not invent unseen state.

### 2.2 Read-mostly by default
Default posture:
- read current system state;
- summarize it;
- propose actions;
- wait for confirmation before mutating anything.

### 2.3 Two write paths
There are two distinct write-back paths:

1. **Operational write-back**
   - update watchlists
   - snooze / claim / resolve inquiries
   - approve or reject action proposals
   - annotate postmortems
   - pause or resume a source
   - create notes, plans, or tasks

2. **Implementation write-back**
   - change repo files
   - add tests
   - modify prompts
   - update configuration
   - prepare migrations or code patches

Operational write-back goes through Event OS command APIs.
Implementation write-back uses Claude Code's standard repository tools and must be separately authorized.

### 2.4 Side effects are explicit
A chat message never directly mutates the system.
It first becomes:
- an extracted intent,
- then a proposal,
- then (if confirmed / auto-authorized by policy) a command execution.

### 2.5 Structured reasoning trace, not raw chain-of-thought
Store and expose:
- retrieved evidence references,
- hypotheses,
- selected reasoning path,
- counterarguments,
- confidence changes,
- reason codes,
- action proposals,
- execution outcomes.

Do not rely on or expose hidden scratchpad text.

## 3. High-level topology

```text
User <-> Claude Code UI
          |
          +-- skills (/ops-chat, /ops-apply, /ops-implement)
          +-- hooks (logging, permission fences, audit)
          +-- agents (ops copilot, ops auditor)
          +-- MCP tools
                  |
                  +-- Read MCP Server
                  |     - get_global_status
                  |     - get_symbol_dossier
                  |     - get_inquiry_inbox
                  |     - get_recent_events
                  |     - get_decision_dossier
                  |     - get_trade_history
                  |     - search_context_capsules
                  |
                  +-- Control MCP Server
                  |     - create_note
                  |     - create_inquiry
                  |     - snooze_inquiry
                  |     - approve_proposal
                  |     - reject_proposal
                  |     - pause_source
                  |     - resume_source
                  |     - update_watchlist
                  |     - create_plan
                  |
                  +-- Admin / Impl MCP Server (restricted)
                        - arm_live
                        - change_threshold
                        - register_source_candidate
                        - create_repo_task
                        - open_patch_plan
```

## 4. New runtime components

### 4.1 Ops Context Assembler
Builds compact, queryable context capsules from ledgers and metrics.

### 4.2 Chat Session Manager
Tracks sessions, messages, mode, actor, active scope, and pending proposals.

### 4.3 Intent Extractor
Parses user messages into structured intents such as:
- ask_status
- ask_why
- ask_plan
- annotate
- approve
- reject
- snooze
- create_inquiry
- update_watchlist
- request_patch
- request_threshold_change

### 4.4 Action Proposal Engine
Turns mutating intents into explicit proposals with:
- target object
- expected effect
- diff preview
- risk level
- confirmation requirement
- rollback hint

### 4.5 Action Reflector
After execution, writes effects back into:
- chat state,
- notes,
- ledgers,
- outbox,
- context capsules.

### 4.6 Chat Memory Projector
Selectively promotes useful chat outcomes into durable system knowledge:
- operator notes
- rationale notes
- recurring operating constraints
- future follow-up items

## 5. Modes

The copilot has four runtime modes.

### 5.1 Observe
Read-only. Answer and summarize.

### 5.2 Advise
Can produce action proposals but not execute them.

### 5.3 Operate
Can execute operational commands within RBAC + confirmation policy.

### 5.4 Implement
Can also modify repository/configuration artifacts via Claude Code tools.
This mode must be:
- opt-in,
- time-boxed,
- audited,
- visibly indicated to the operator.

## 6. Core object model

### 6.1 Context Capsule
A summary object produced from one or more ledgers / sources.

### 6.2 Chat Session
The conversational container.

### 6.3 Chat Message
A user, assistant, tool, or system utterance.

### 6.4 Chat Intent
The parsed user goal.

### 6.5 Chat Action Proposal
A candidate mutation with preview and risk metadata.

### 6.6 Chat Action Execution
The realized effect of a proposal.

### 6.7 Chat Note
A promoted memory artifact from conversation.

## 7. Primary use cases

### 7.1 Explain current status
"Why are we bearish on NVDA right now?"
Answer from:
- recent events,
- latest forecast,
- macro regime,
- counterarguments,
- confidence drift,
- current position state.

### 7.2 Explain actions taken
"What trades did the system place today and why?"
Answer from orders, decisions, reason codes, and plan lineage.

### 7.3 Create follow-up work
"Keep an eye on FDA news for LLY this week."
Convert to inquiry or source-plan update.

### 7.4 Approve a proposal
"Okay, snooze that question for 2 hours."
Convert to proposal -> execute -> reflect.

### 7.5 Patch the implementation
"The inquiry list is noisy. Add a stricter grouping rule."
Open implementation mode, inspect code, draft patch plan, modify repo, run tests, summarize diff.

## 8. Non-goals for v1
- free-form social chat;
- hidden thought dumps;
- automatic high-risk system mutation without approval;
- full multi-user collaboration semantics beyond simple claim/assignment;
- replacing Grafana dashboards.

## 9. Required integrations
- existing ledgers
- outbox events
- RBAC / auth
- Human Inquiry Orchestration
- source registry and watch planner
- Grafana links for dashboards
- Claude Code plugin / skills / hooks / MCP surface
