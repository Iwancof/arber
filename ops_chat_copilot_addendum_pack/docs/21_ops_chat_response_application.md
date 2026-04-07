# 21. Chat Response Application Layer (How Chat Changes the System)

## 1. Objective

Turn selected chat messages into safe system mutations with:
- intent extraction,
- proposal preview,
- approval policy,
- execution,
- reflection,
- audit.

## 2. Mutation pipeline

```text
user message
  -> chat_intent
  -> action proposal
  -> confirmation / auto-policy decision
  -> command execution
  -> ledger / outbox writes
  -> context refresh
  -> assistant follow-up
```

## 3. Intent classes

### Read-only intents
- ask_status
- ask_why
- ask_what_changed
- ask_plan
- ask_trade_history
- ask_source_coverage
- ask_inquiry_backlog

### Low-risk operational intents
- create_note
- create_inquiry
- snooze_inquiry
- claim_inquiry
- resolve_inquiry
- reject_proposal
- approve_proposal
- pause_source
- resume_source
- update_watchlist_soft

### Medium-risk operational intents
- update_threshold_candidate
- register_source_candidate
- shift_priority
- enable_source_bundle_provisional

### High-risk intents
- arm_live
- disable kill switch
- change broker / market profile
- mutate production config
- edit repository implementation

## 4. Proposal model

Every mutating intent becomes a proposal.

Proposal fields:
- target entity
- requested effect
- exact command(s)
- diff preview
- reason
- risk tier
- required approval count
- expiry
- rollback hint
- blocked-by policy list

## 5. Confirmation policy

### 5.1 Auto-apply allowed
Only for tiny safe operations such as:
- mark message read
- create personal note
- open read-only dossier
- create draft inquiry in shadow mode

### 5.2 Single confirmation
Default for low-risk operational changes.

### 5.3 Dual confirmation / typed confirmation
Required for:
- live arming
- kill switch changes
- threshold changes affecting execution
- source bundle changes on active markets
- repo edits in implementation mode if touching production-critical files

## 6. Reflection

After execution, the system should write back:
- execution result
- related ledger ids
- generated outbox events
- updated context capsule refs
- user-visible summary
- whether further follow-up is needed

## 7. Chat memory projection

Selected chat outputs should be promoted into durable notes.

### Promote if:
- the user states a durable operating preference;
- a repeated constraint is clarified;
- a rationale should be attached to a case or symbol;
- a future follow-up action is created.

### Do not promote:
- ephemeral chit-chat;
- stale speculation;
- unapproved risky proposals;
- raw hidden reasoning.

## 8. Implementation-mode path

Implementation mode is special.

### Entry conditions
- explicit user request
- capability `can_repo_modify`
- mode switch visible in session
- audit entry created

### Behavior
- Claude Code may read/edit repo files and run tests
- system changes still go through explicit review
- resulting patch summary is reflected into chat and linked to repo diff

### Exit
- mode expires automatically
- session returns to observe or advise

## 9. Safety fences

### 9.1 No silent side effects
No hidden writes from plain explanation answers.

### 9.2 No direct tool free-for-all
Chat agent does not get unrestricted write tools by default.

### 9.3 Immutable audit
Every proposal and execution is ledgered.

### 9.4 Role-aware tool set
Observe mode exposes read-only MCP.
Operate mode exposes constrained control MCP.
Implement mode additionally permits repo tools.

## 10. Failure paths

If extraction confidence is low:
- ask clarification
- or emit proposal in draft status
- or store message as note without mutation

If execution fails:
- mark proposal failed
- preserve result payload
- surface rollback guidance
- refresh context so chat answers remain honest

## 11. Required tables
- `ops_chat.chat_session`
- `ops_chat.chat_message`
- `ops_chat.chat_intent`
- `ops_chat.chat_action_proposal`
- `ops_chat.chat_action_execution`
- `ops_chat.chat_memory_note`

## 12. Required APIs
- create/list chat sessions
- post chat message
- list proposals
- confirm/reject proposal
- create note
- list context capsules
- create repo task / patch plan
- list execution history

## 13. v1 recommendation

v1 should implement:
- read-only Q&A
- note creation
- inquiry operations
- source pause/resume
- watchlist update
- proposal approval/rejection

Do not ship live arming or production repo mutation in auto mode in v1.
