# 20. Ops Context Assembly (Information Summarization Layer)

## 1. Objective

Create a durable, queryable representation of current system state that is suitable for:
- chat answers,
- UI cards,
- chart annotations,
- inboxes,
- dossiers,
- postmortems,
- alert explanations.

The chat assistant should almost never query raw ledgers directly for every answer.  
Instead it should prefer **context capsules**: structured summaries with provenance.

## 2. Why capsules

Raw ledgers are:
- too granular,
- too wide,
- expensive to join repeatedly,
- hard to present cleanly in chat,
- not optimized for freshness-aware explanation.

Capsules solve this by pre-assembling the highest-value operational views.

## 3. Capsule taxonomy

### 3.1 Global Status Capsule
Contains:
- current execution mode;
- live / paper arm state;
- kill switch state;
- active market profiles;
- source health;
- inquiry backlog;
- top risk flags;
- latest operational incidents.

### 3.2 Market Regime Capsule
Contains:
- current macro regime classification;
- drivers;
- confidence;
- effective period;
- expected sensitive assets;
- important upcoming macro events.

### 3.3 Symbol Dossier Capsule
Contains:
- latest relevant events;
- current forecast and confidence;
- open inquiry links;
- active or recent decisions;
- orders and realized outcomes;
- key risks and no-trade conditions;
- source coverage status.

### 3.4 Inquiry Case Capsule
Contains:
- case summary;
- why it was created;
- pending tasks;
- deadlines;
- superseded tasks;
- user responses;
- auto-only fallback state.

### 3.5 Trade / Decision Dossier Capsule
Contains:
- decision summary;
- forecast basis;
- risk gates passed/failed;
- order status;
- outcome to date;
- postmortem if available.

### 3.6 Portfolio / Exposure Capsule
Contains:
- open positions;
- sector / theme concentration;
- execution mode and safety posture;
- current hedge picture;
- live risk flags.

### 3.7 Recent Changes Capsule
Contains:
- what changed in the last N minutes/hours;
- new inquiries;
- new forecasts;
- changed kill switches;
- new/changed source plans;
- orders placed / canceled / rejected.

### 3.8 Ops Backlog Capsule
Contains:
- pending proposals;
- expired prompts;
- stuck inquiries;
- failing sources;
- failed workers;
- unresolved incidents.

## 4. Capsule generation lifecycle

### 4.1 Event-driven refresh
Refresh when important state changes, such as:
- event created
- forecast created
- decision created
- order status changed
- inquiry task created or answered
- source paused/resumed
- kill switch changed

### 4.2 Time-based refresh
Also refresh on TTL schedules because some summaries age even without new writes.

Suggested TTL:
- Global status: 30s
- Market regime: 60s
- Symbol dossier: 60s to 5m depending on active interest
- Inquiry case: 30s
- Portfolio: 30s
- Recent changes: 15s

### 4.3 On-demand refresh
If the chat assistant requests a missing or stale capsule, the assembler can rebuild it synchronously or queue a refresh.

## 5. Capsule structure

Each capsule should include:

```json
{
  "capsule_id": "uuid",
  "capsule_type": "symbol_dossier",
  "scope_key": "AAPL",
  "generated_at": "2026-04-07T12:34:56Z",
  "fresh_until": "2026-04-07T12:35:56Z",
  "summary_md": "...",
  "summary_json": {
    "state": "...",
    "drivers": [],
    "open_questions": [],
    "risks": [],
    "reason_codes": []
  },
  "evidence_refs": [
    {"kind":"event","id":"..."},
    {"kind":"forecast","id":"..."},
    {"kind":"decision","id":"..."}
  ],
  "trace_id": "..."
}
```

## 6. Input sources

Capsules may draw from:
- `event_ledger`
- `forecast_ledger`
- `decision_ledger`
- `order_ledger`
- `outcome_ledger`
- `postmortem_ledger`
- `inquiry_case/task/response`
- `source_registry`, `watch_plan`, `watcher_instance`
- auth / mode state
- observability summaries
- operator notes
- chat proposal / execution history

## 7. Freshness rules

Chat answers must report freshness explicitly when it matters.

Rules:
- if capsule is fresh: answer directly;
- if capsule is stale but within grace window: answer with freshness warning and optionally refresh;
- if capsule is stale beyond grace window: refresh before answering or state that freshness is unknown.

## 8. Provenance requirements

Every answerable fact should be traceable to source objects.

Minimum provenance types:
- `ledger_ref`
- `document_ref`
- `inquiry_ref`
- `proposal_ref`
- `execution_ref`
- `metrics_snapshot_ref`

## 9. Suggested materialization strategy

### 9.1 DB tables
- `ops_chat.context_capsule`
- `ops_chat.context_capsule_source_ref`
- `ops_chat.context_capsule_refresh_job`

### 9.2 Storage split
- summary and JSON in Postgres
- larger raw evidence bundles remain in existing stores
- optional object storage for large rendered dossiers

### 9.3 Indexing
Index by:
- `capsule_type`
- `scope_key`
- `generated_at desc`
- `fresh_until`
- `is_active`

## 10. Answer composition pattern

The chat assistant should compose answers in this order:
1. retrieve relevant capsule(s)
2. check freshness
3. retrieve missing fine-grained evidence if needed
4. answer with:
   - current state
   - why
   - what changed
   - what is uncertain
   - what the system plans next

## 11. Chart overlay support

The same capsule store should feed overlay annotations:
- forecast issued
- inquiry created / answered / expired
- decision created / rejected
- order submitted / filled / canceled
- regime changed

## 12. Failure handling

If capsule generation fails:
- keep previous capsule if still within stale grace window
- mark status as degraded
- emit outbox event
- show stale/degraded badge in chat and UI

## 13. v1 scope

Implement these capsule types first:
- global_status
- market_regime
- symbol_dossier
- inquiry_case
- decision_dossier
- recent_changes

Leave portfolio and complex multi-market dossier variants for later.
