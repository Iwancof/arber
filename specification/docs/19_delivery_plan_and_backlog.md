# 19. Delivery Plan and Backlog

## 19.1 フェーズ方針

### Phase 0: skeleton
- DB schemas
- registries
- Grafana shell
- operator API skeleton
- sample dashboards

### Phase 1: ingest and ledgers
- source registry
- watch planner
- raw_document ingest
- dedupe
- event ledger
- event inbox

### Phase 2: forecast and dossier
- retrieval
- forecast worker
- decision ledger
- dossier page
- overlay panel

### Phase 3: manual bridge and replay
- prompt console
- prompt task lifecycle
- replay engine
- judge/postmortem

### Phase 4: paper and micro-live
- broker adapter
- execution modes
- order ledger
- drift dashboards

### Phase 5: extensibility hardening
- plugin registry
- schema registry
- source candidate flow
- additional markets pilot

## 19.2 Epic 一覧

- EPIC-A Core Registries
- EPIC-B Ingest Pipeline
- EPIC-C Event Extraction
- EPIC-D Forecast/Decision
- EPIC-E Grafana Shell and Plugins
- EPIC-F Manual Expert Bridge
- EPIC-G Replay/Validation
- EPIC-H Broker Integration
- EPIC-I Observability/Security
- EPIC-J Extensibility Platform

## 19.3 依存関係

- UI dossier depends on decision API + overlay API
- execution depends on decision ledger + broker adapter
- source candidate depends on source registry + metrics
- plugin registry depends on authz + config store
- replay depends on ledger integrity + market profile snapshots

## 19.4 Exit Criteria

### Phase 1 exit
- new raw documents visible in inbox
- events extracted and verifiable
- watchers observable in Grafana

### Phase 2 exit
- dossier shows forecast, evidence, reasoning
- overlay panel functional
- decisions persisted

### Phase 3 exit
- prompt tasks can be created, validated, accepted/rejected
- replay reproducible
- postmortems generated

### Phase 4 exit
- paper mode end-to-end
- adjusted paper P/L computed
- micro-live gated and safe

### Phase 5 exit
- source candidate lifecycle works
- new market can be added without core code change
- plugin manifest enforced

## 19.5 Team Shape

- Tech Lead / Architect
- Backend x2
- UI/Grafana x1-2
- Data/ML x1
- SRE/Platform x1
- QA/Validation x1
- Product/Operator representative x1

## 19.6 What to postpone

- multi-broker routing
- tenantization
- arbitrary user strategies
- full plugin marketplace
- overnight live trading for all markets
