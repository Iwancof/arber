# 04. Core Workflows and Failure Paths

## 4.1 主要ワークフロー一覧

1. realtime source ingest
2. scheduled macro ingest
3. event extraction + verification
4. retrieval + forecast + decision
5. manual expert escalation
6. replay and shadow evaluation
7. order routing and fill handling
8. outcome build + judge + postmortem
9. source candidate onboarding
10. plugin deployment / dashboard rollout

## 4.2 Realtime Source Ingest

### 正常フロー
1. watcher starts
2. source endpoint fetch/stream
3. raw_document persisted
4. dedupe check
5. document_asset_link create/update
6. extraction task emit

### 失敗パス
- fetch timeout -> retry with backoff
- parser drift -> dead-letter queue + source degraded
- duplicate storm -> cluster expansion guard
- asset link ambiguous -> mark uncertain, continue extraction

## 4.3 Scheduled Macro Ingest

### 正常フロー
1. watch planner loads market_profile calendar rules
2. release schedule creates pre-release window
3. source endpoint fetched at release time
4. event extraction and macro regime task triggered
5. decision engine may set `macro_release_hold`

### 失敗パス
- calendar mismatch -> alert + manual override
- release delayed -> keep watcher open within grace window
- source unavailable -> secondary source fallback if allowed

## 4.4 Event Extraction + Verification

### 正常フロー
1. raw doc selected
2. worker task generated with bounded evidence
3. extractor returns structured event
4. verifier checks schema, enums, citations, timestamps
5. event ledger appended
6. impacts linked to instruments and benchmarks

### 失敗パス
- schema invalid -> reformat task
- evidence span invalid -> reject extraction
- event type unknown -> classify as provisional type + review queue
- contradictory evidence -> mark verification_status = disputed

## 4.5 Forecast + Decision

### 正常フロー
1. event selected
2. retrieval set built
3. forecast worker outputs distribution
4. skeptic / baseline run
5. meta scorer computes score
6. policy engine returns no-trade / propose / wait-manual / execute
7. decision ledger appended

### 失敗パス
- retrieval empty -> low confidence + no-trade
- worker timeout -> fallback model or no-trade
- conflicting inputs -> escalate manual
- policy pack missing for market -> market disabled

## 4.6 Manual Expert Bridge

### 正常フロー
1. decision hits escalation policy
2. prompt_task created
3. operator sees prompt pack in Prompt Console
4. external Web LLM used manually
5. response pasted back
6. parser + schema validation
7. response weighted and linked to decision
8. meta scorer reruns if configured

### 失敗パス
- deadline exceeded -> fallback to auto-only path
- invalid schema -> reformat flow
- forbidden evidence reference -> reject
- operator injects external facts -> reject + audit flag

## 4.7 Order Routing

### 正常フロー
1. decision approved
2. risk gate checks mode, session, kill switch, exposure cap
3. broker adapter maps intent to order
4. order submitted
5. order update stream updates order ledger
6. fill updates position state

### 失敗パス
- broker reject -> reject reason logged + policy cooldown
- partial fill -> position updates incrementally
- session closed -> park or cancel based on policy
- connectivity loss -> reconcile orders on reconnect

## 4.8 Outcome + Postmortem

### 正常フロー
1. horizon reached
2. outcome builder computes realized relative returns and barriers
3. judge task runs
4. postmortem ledger appended
5. reliability store updated
6. source gap stats updated
7. source scout may generate candidate

### 失敗パス
- price data missing -> pending outcome state
- corporate action mismatch -> adjusted/raw split outcome
- judge invalid -> retry or mark human review

## 4.9 Source Candidate Onboarding

### 正常フロー
1. source scout proposes candidate
2. operator reviews
3. provisional state with dry-run fetch
4. parser metrics recorded
5. candidate validated
6. production promotion approved

### 失敗パス
- legal issue -> immediate rejected
- unstable endpoint -> remain provisional
- high noise / low contribution -> retire
- same coverage already saturated -> bundle-level reject

## 4.10 Compensating Actions

- duplicate raw docs -> cluster and merge references
- bad event extraction -> append corrected event + correction link
- wrong order intent in paper/shadow -> cancel workflow and flag
- schema change rollout failure -> dual-read old+new schema until fixed
