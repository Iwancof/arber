# 23. Autonomous News Exploration and Universe Discovery Addendum

## 1. Purpose

This addendum introduces a persistent research subsystem that does two things in parallel:

1. **Context Deepening for watched symbols**  
   Continuously collect historical news, filings, prior event analogs, peer moves, and counterarguments for symbols that are already in the active universe, pending inquiry queue, candidate list, or open positions.

2. **Universe Discovery for not-yet-watched symbols**  
   Detect symbols that are repeatedly implicated by current news flow, sector ripple effects, peer reactions, supply-chain links, official disclosures, or unusual co-mention patterns, and promote them into a monitored universe only when evidence quality clears a threshold.

The goal is not to make the system “read more news” in the abstract. The goal is to make the system **build and refresh decision context**.

This subsystem must improve:
- inquiry quality
- forecast quality
- operator situational awareness
- symbol coverage breadth without causing uncontrolled noise
- postmortem quality by preserving historical context

## 2. Non-goals

This subsystem is **not** a fully autonomous order generator.
It must not:
- place orders directly
- auto-promote every mentioned ticker into the tradable universe
- rely on unbounded crawling
- replace event extraction, forecasting, or policy decisions
- write free-form “research notes” without evidence traceability

It is an evidence-harvesting and context-structuring layer.

## 3. Core design principles

### 3.1 Evidence first
Every research artifact must be linked to bounded evidence:
- raw documents
- event records
- historical filings
- prior postmortems
- source metadata
- market data snapshots

No ungrounded “research memory” should exist.

### 3.2 Separate deepening from discovery
Use two loops:
- **Context Deepener** = gather more material on symbols already known to matter
- **Universe Discovery Scout** = search for symbols not yet in the watchlist

These loops have different budgets, different thresholds, and different failure modes.

### 3.3 Promotion, not sprawl
The system may observe many symbols, but only a bounded set should become:
- actively watched
- eligible for inquiry generation
- eligible for manual review
- eligible for policy scoring

A candidate symbol must be promoted through a controlled workflow.

### 3.4 Case-centric memory
Research work should be organized by **case**, not just by ticker.
Examples:
- “NVDA supply-chain spillover into AVGO and TSM”
- “Biotech approval cluster affecting large-cap pharma peers”
- “Tesla regulatory win versus analyst downgrade conflict”
- “Banks with repeated buyback signals under rate repricing”

A case can contain multiple symbols, events, and hypotheses.

### 3.5 Research is optional but persistent
Research jobs should run continuously and enrich context, but the main system must remain operational if research is delayed, stale, or paused.

### 3.6 Budgeted autonomy
The subsystem should obey:
- source budgets
- token budgets
- query budgets
- candidate universe limits
- per-market and per-sector caps

This prevents endless exploration and keeps operator attention usable.

## 4. Functional overview

## 4.1 Subsystems

### A. Context Deepener
Inputs:
- watched symbols
- open positions
- wait_manual decisions
- high-materiality inquiries
- symbols with repeated conflicting evidence
- postmortem failure code `insufficient_context` or `peer_context_missing`

Outputs:
- symbol dossier updates
- historical analog bundles
- peer impact bundles
- counterargument bundles
- refreshed research brief
- inquiry suggestions when uncertainty remains high

### B. Universe Discovery Scout
Inputs:
- incoming event stream
- symbol co-mentions
- sector ripple detections
- repeated peer moves
- source gap signals
- operator themes / manual watch directives
- large market-cap names not yet watched but repeatedly relevant

Outputs:
- candidate symbols
- candidate promotion proposals
- relation edges to currently watched symbols
- source bundle suggestions for new sectors/regions

### C. Research Case Orchestrator
Maintains:
- research cases
- scopes
- jobs
- evidence bundles
- dossier snapshots
- candidate lifecycle

### D. Research Brief Composer
Turns evidence into bounded, structured summaries:
- current thesis
- bull points
- bear points
- unresolved questions
- known analogs
- missing evidence
- recommended next research actions

### E. Promotion Gate
Decides whether a candidate symbol becomes:
- monitored only
- fully watched
- inquiry-eligible
- policy-eligible
- retired / rejected

This gate is deterministic with optional LLM explanation, not pure LLM discretion.

## 5. Data flow

```text
[Existing Event Stream / Inquiries / Decisions / Postmortems]
                        |
                        v
             [Research Signal Evaluator]
                        |
          +-------------+-------------+
          |                           |
          v                           v
 [Context Deepener Planner]   [Universe Discovery Planner]
          |                           |
          v                           v
 [Research Jobs + Query Plans + Retrieval Tasks]
          |                           |
          +-------------+-------------+
                        |
                        v
                 [Evidence Store]
                        |
                        v
             [Research Brief Composer]
                        |
          +-------------+-------------+
          |                           |
          v                           v
 [Symbol Dossier Snapshot]   [Candidate Promotion Queue]
          |                           |
          v                           v
 [Ops Chat / Inquiry / UI]    [Universe Manager / Source Planner]
```

## 6. When the subsystem should trigger

## 6.1 Context deepening triggers
Create or refresh a research case when any of the following occurs:
- symbol is currently in active watchlist
- symbol has an open paper/live position
- symbol has `wait_manual` decision
- event has high materiality but confidence is in a middle band
- skeptic_review says `missing_peer_context` or `insufficient_history`
- postmortem says:
  - `source_gap`
  - `context_missing`
  - `peer_miss`
  - `regime_mismatch`
- multiple events for same issuer arrive within a rolling window
- opposing events arrive for same issuer or same sector

## 6.2 Universe discovery triggers
Create a candidate or discovery case when any of the following occurs:
- symbol repeatedly appears with watched symbols across independent documents
- a peer reaction suggests second-order beneficiaries or losers
- index / ETF / supplier / customer / competitor relationships are implied
- a macro event causes a strong move in a sector where coverage is thin
- official disclosure references a parent, subsidiary, acquirer, target, partner, or key customer not yet watched
- inquiry resolution repeatedly says “this would be easier if we also monitored X”
- watchlist diversity for a sector/region is below configured floor

## 7. Research case model

A **research case** is the primary organizing unit.

### 7.1 Case types
- `symbol_context`
- `sector_context`
- `theme_context`
- `cross_symbol_spillover`
- `universe_discovery`
- `source_gap_investigation`
- `postmortem_followup`

### 7.2 Case states
- `new`
- `monitoring`
- `enriching`
- `awaiting_human`
- `promotion_pending`
- `resolved`
- `retired`

### 7.3 Case scopes
A case may scope:
- one primary symbol
- related symbols
- one or more sectors
- one theme
- one market profile
- one source bundle

## 8. Symbol dossier concept

A **symbol dossier** is a bounded snapshot for one symbol. It should not be a raw dump.

It should contain:
- current benchmark
- current market/sector profile
- latest major events
- last 5-10 relevant historical analogs
- bull thesis bullets
- bear thesis bullets
- unresolved questions
- repeated failure patterns from postmortem
- related symbols and why they matter
- source coverage level
- research freshness timestamp

### 8.1 Dossier freshness
Dossiers should have freshness classes:
- `fresh` (< 24h for active watched symbols)
- `warm` (< 72h)
- `stale`
- `archived`

### 8.2 Dossier refresh policy
- open positions: daily
- wait_manual: immediate + daily refresh
- active watched symbols: daily or on material event
- candidate symbols: refresh only on trigger
- retired symbols: refresh only if rediscovered

## 9. Universe discovery model

## 9.1 Candidate symbol lifecycle
- `new`
- `monitoring`
- `needs_more_evidence`
- `promotion_pending`
- `promoted`
- `rejected`
- `expired`

## 9.2 Discovery score
Candidate symbols should have a deterministic `discovery_score` built from:
- co-mention frequency with watched symbols
- relation strength to watched symbols
- source quality
- recurrence across independent documents
- market-cap / liquidity floor
- novelty
- sector coverage deficit
- evidence freshness
- existing watchlist overlap
- operator interest tags

LLM may explain the score, but the score should not be produced solely by the LLM.

## 9.3 Promotion rules
A candidate should be promoted only if:
- evidence comes from bounded sources
- at least one relation to current universe is explicit or strongly inferred
- candidate meets market/liquidity filters
- discovery score exceeds threshold
- candidate is not redundant with already watched peers
- candidate does not exceed per-sector or per-market caps

Promotion outcomes:
- `observe_only`
- `watchlist_add`
- `inquiry_eligible`
- `policy_eligible`
- `reject`

## 10. Research retrieval strategy

## 10.1 Retrieval buckets
For each research job, the system may search across:
- recent news
- historical news
- official filings
- past event ledgers
- postmortems
- inquiry history
- peer symbol events
- benchmark and sector events
- source registry metadata

## 10.2 Query plan types
- `symbol_backfill`
- `event_analog_search`
- `peer_scan`
- `theme_scan`
- `relation_confirmation`
- `counterargument_search`
- `source_probe`
- `candidate_validation`

## 10.3 Retrieval horizon defaults
- recent event follow-up: 7d / 30d
- analog search: 90d / 1y / 3y
- peer context: 30d / 90d
- candidate validation: 30d
- source gap investigation: depends on missed case window

## 11. Research outputs

## 11.1 Structured research brief
Every brief should stay bounded and machine-usable.

Suggested JSON shape:

```json
{
  "brief_kind": "symbol_context",
  "primary_symbol": "TSLA",
  "benchmark_symbol": "SPY",
  "current_thesis": "Recent analyst downgrades dominate the short-term signal, but regulatory support may soften downside persistence.",
  "bull_points": [
    {"code": "regulatory_tailwind", "weight": 0.32, "evidence_refs": ["e1", "e3"]}
  ],
  "bear_points": [
    {"code": "analyst_cluster_downgrade", "weight": 0.48, "evidence_refs": ["e2", "e4"]}
  ],
  "related_symbols": [
    {"symbol": "RIVN", "relation_type": "peer", "importance": 0.41}
  ],
  "historical_analogs": [
    {"case_ref": "rc_123", "similarity": 0.72}
  ],
  "unresolved_questions": [
    "Was the regulatory item new information or already priced in?"
  ],
  "recommended_next_actions": [
    "confirm premarket relative move vs auto peers",
    "retrieve prior analyst-cluster downgrade cases"
  ]
}
```

## 11.2 Research signals to downstream systems
This subsystem should emit structured signals such as:
- `research_case.created`
- `research_case.updated`
- `research_brief.refreshed`
- `candidate_symbol.created`
- `candidate_symbol.promoted`
- `candidate_symbol.rejected`
- `symbol_dossier.updated`
- `source_bundle.recommended`

These must go through the same outbox/event discipline as the rest of the platform.

## 12. UI requirements

## 12.1 Research Radar
A Grafana app/plugin page showing:
- active research cases
- stale dossiers
- candidate promotion queue
- sectors with low coverage
- symbols with repeated evidence accumulation
- recently discovered related symbols

## 12.2 Symbol Dossier page
Per-symbol page showing:
- price chart + event annotations
- current dossier summary
- research brief
- related symbol graph
- evidence timeline
- pending inquiries
- promotion history

## 12.3 Discovery Inbox
Queue of candidate symbols with:
- why discovered
- which watched symbols they relate to
- source quality
- promotion recommendation
- accept/reject/snooze controls

## 12.4 Historical Analog Explorer
Searchable view for prior cases by:
- event_type
- symbol
- benchmark
- sector
- verdict
- failure code
- similarity band

## 13. Database extension

Use a dedicated schema such as `research_ops`.

### 13.1 New core tables
- `research_case`
- `research_scope`
- `research_job`
- `research_query_plan`
- `research_evidence`
- `research_brief`
- `symbol_dossier_snapshot`
- `candidate_symbol`
- `related_symbol_edge`
- `research_feedback`

### 13.2 Design notes
- all major objects need `trace_id`, `correlation_id`, `created_at`, `updated_at`
- append-first where possible
- current snapshot tables may coexist with append-only ledgers
- promotion actions must be auditable
- evidence should link back to canonical raw docs/events, not copy content blindly

## 14. API extension

Minimum endpoints:

- `POST /v1/research/cases`
- `GET /v1/research/cases`
- `GET /v1/research/cases/{case_id}`
- `POST /v1/research/jobs`
- `GET /v1/research/jobs`
- `GET /v1/research/symbols/{symbol}/dossier`
- `GET /v1/research/candidates`
- `POST /v1/research/candidates/{candidate_id}/promote`
- `POST /v1/research/candidates/{candidate_id}/reject`
- `POST /v1/research/candidates/{candidate_id}/snooze`
- `POST /v1/research/cases/{case_id}/refresh`
- `GET /v1/research/analogs`

## 15. Prompt/worker additions

Add worker roles:

### 15.1 `context_deepener`
Responsibilities:
- plan what additional evidence is worth fetching
- identify missing context
- propose bounded search queries
- summarize analogs and counterarguments

### 15.2 `universe_discovery_scout`
Responsibilities:
- detect new relevant symbols
- explain relation to existing universe
- avoid broad watchlist inflation
- recommend observe/watch/policy promotion level

### 15.3 `candidate_promotion_reviewer`
Responsibilities:
- decide whether evidence is sufficient to promote
- explicitly note redundancy risk, liquidity risk, and source weakness

### 15.4 `research_brief_composer`
Responsibilities:
- compress evidence into a structured dossier-ready brief
- preserve bull/bear balance
- keep unresolved questions explicit

## 16. Budgeting and caps

## 16.1 Global budgets
The subsystem must expose configurable caps:
- max active research cases per market
- max candidate symbols per sector
- max discovery jobs per hour
- max deepening jobs per symbol per day
- max historical backfill docs per job
- LLM token budget per day
- source polling budget per day

## 16.2 Suggested v1 defaults
- active research cases: 50
- promotion-pending candidates: 20
- candidates per sector: 5
- deepening refresh per active watched symbol: 1/day
- analog docs per job: 25
- discovery jobs per hour: 12

## 17. Safety rules

- no direct trading authority
- no auto-promotion to tradable universe without deterministic checks
- no use of community sources as sole evidence for promotion
- no unbounded recursive discovery
- no candidate promotion if source quality is below threshold
- no stale dossier used as primary justification for trade without refresh
- no research brief without explicit unresolved questions when evidence conflict exists

## 18. Metrics

### 18.1 Coverage metrics
- watchlist coverage by sector
- average dossier freshness
- candidate discovery rate
- promotion rate
- rejected candidate rate
- source coverage depth

### 18.2 Quality metrics
- % of inquiries improved by research context
- % of postmortems citing research evidence
- candidate promotion precision
- dossier refresh success rate
- analog relevance click/open rate
- source gap recurrence after research rollout

### 18.3 Operator usability metrics
- time from inquiry to usable context
- number of stale dossiers at market open
- number of candidates awaiting review > SLA
- operator acceptance rate for promotion proposals

## 19. Implementation phases

## Phase A
- create schema and APIs
- implement research_case, candidate_symbol, symbol_dossier_snapshot
- add manual refresh endpoint
- build Research Radar and Dossier UI

## Phase B
- implement Context Deepener planner
- historical analog retrieval
- structured research brief generation
- emit research outbox events

## Phase C
- implement Universe Discovery Scout
- candidate promotion queue
- relation graph
- source bundle recommendation

## Phase D
- integrate with inquiry and ops chat
- use dossiers in chatbot answers
- use candidate promotions to update universe/source planner
- add postmortem feedback loop

## 20. Final design stance

This subsystem should make the platform feel like it is *accumulating understanding*, not merely reacting to the latest headline.

The correct mental model is:
- **event stream** tells us what just happened
- **forecast layer** tells us what it may mean
- **research scout** tells us what context we are still missing and which additional symbols now matter
- **ops chat** turns this accumulated context into operator-usable decisions
