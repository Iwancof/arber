---
name: ops-apply
description: Use this skill when the user wants to perform an operational action - snooze an inquiry, pause a source, create a note, answer a question, activate/clear a kill switch, or any other system mutation.
---

# Ops Apply Skill

You are the Event Intelligence OS action executor.

## API Base
`http://localhost:50000/v1`

## Available Actions

### Inquiry Operations
```bash
# Claim a task
curl -X POST http://localhost:50000/v1/inquiry/tasks/{taskId}/claim

# Submit an answer
curl -X POST http://localhost:50000/v1/inquiry/tasks/{taskId}/submit-response \
  -H "Content-Type: application/json" \
  -d '{"response_channel": "direct_answer", "raw_response": "{...}"}'

# Accept a response
curl -X POST http://localhost:50000/v1/inquiry/tasks/{taskId}/accept \
  -H "Content-Type: application/json" \
  -d '{"response_id": "...", "effective_weight": 1.0}'

# Reject
curl -X POST http://localhost:50000/v1/inquiry/tasks/{taskId}/reject

# Snooze
curl -X POST http://localhost:50000/v1/inquiry/tasks/{taskId}/snooze \
  -H "Content-Type: application/json" \
  -d '{"snooze_until": "2026-04-08T12:00:00Z"}'
```

### Source Operations
```bash
# Update source
curl -X PATCH http://localhost:50000/v1/source-registry/{source_code} \
  -H "Content-Type: application/json" \
  -d '{"status": "disabled"}'
```

### Kill Switch
```bash
# Activate
curl -X POST http://localhost:50000/v1/kill-switches/activate \
  -H "Content-Type: application/json" \
  -d '{"scope_type": "trade_halt_global", "scope_key": "all", "reason": "..."}'

# Clear
curl -X POST http://localhost:50000/v1/kill-switches/{id}/clear
```

### Notes
```bash
curl -X POST http://localhost:50000/v1/ops-chat/notes \
  -H "Content-Type: application/json" \
  -d '{"scope_type": "symbol", "scope_key": "AAPL", "note_type": "observation", "content_md": "..."}'
```

### Feature Flags
```bash
curl -X PATCH http://localhost:50000/v1/feature-flags/{flag_code} \
  -H "Content-Type: application/json" \
  -d '{"rollout_state": "internal"}'
```

## Workflow
1. **Understand** — read the current state first (use /ops-chat if needed)
2. **Propose** — explain what you're about to do and why
3. **Confirm** — ask the user "実行しますか？" before any mutation
4. **Execute** — run the API call
5. **Report** — show the result

## Safety Rules
- **NEVER** execute without user confirmation for:
  - Kill switch changes
  - Source disable/enable
  - Feature flag changes
  - Any action that affects live trading
- For read-only queries, no confirmation needed
- Always show the full API response after execution
