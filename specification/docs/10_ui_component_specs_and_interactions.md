# 10. UI Component Specs and Interactions

## 10.1 Overview

この文書は各画面のコンポーネント単位の詳細を定義する。

## 10.2 Market Overlay Dashboard

### 主目的
価格の時間軸に、予測帯・イベント・プロンプト・判断・注文を重ねて把握する。

### レイアウト
- 上段: candlestick + forecast overlay
- 中段: decision timeline / regime ribbon
- 下段: prompt ribbon / order markers / source coverage mini panel
- 右サイド: latest dossier summary

### Overlay tracks
1. median forecast line (`ret_q50`)
2. forecast band (`q10-q90`)
3. downside / upside barriers
4. event annotations
5. prompt task annotations
6. decision intervals
7. order/fill markers
8. position intervals

### Interaction
- click annotation -> Decision Dossier
- hover forecast band -> show confidence and reason codes
- shift+drag -> replay job seed range
- click prompt marker -> Prompt Console task
- filter chips: market, horizon, mode, event_type

## 10.3 Event Inbox

### カード項目
- event type badge
- issuer + affected assets
- source tier
- materiality / novelty
- confidence badge
- current decision status
- prompt status
- source gap flag
- actions

### actions
- open dossier
- mark watch-only
- request manual prompt
- suppress from inbox
- create replay job from event

## 10.4 Decision Dossier

### Header
- symbol
- market
- mode
- current decision
- score
- confidence
- live impact warning

### Tabs
- Summary
- Evidence
- Reasoning
- Manual Bridge
- Baselines
- Orders
- Outcome
- History

### Summary tab
- condensed narrative summary
- no-trade reasons
- selected hypothesis
- top 3 counterarguments
- risk gates triggered

### Evidence tab
- grouped by official / vendor / macro / market snapshot
- evidence span highlight
- doc links and content hash

### Reasoning tab
- hypothesis table
- counterargument table
- confidence change chart
- retrieved cases list

## 10.5 Prompt Console

### Left pane
- task queue
- deadline
- priority
- affected market / symbol
- required schema badge

### Center pane
- prompt pack
- copy button
- evidence snippets
- schema summary

### Right pane
- paste box
- parse result
- schema validation detail
- reliability preview
- accept / reject / request reformat

### safety behavior
- if task impacts live decision, confirm modal required
- external facts detected -> block accept

## 10.6 Source Registry Page

### Grid columns
- source code
- display name
- trust tier
- adapter type
- markets
- tags
- status
- last success
- recent contribution
- parser success rate
- dry-run only badge

### detail drawer
- endpoints
- bundle membership
- recent errors
- sample docs
- promotion history

## 10.7 Postmortem Explorer

### Filters
- market
- symbol
- event type
- failure code
- source gap
- model
- horizon
- mode

### Visuals
- failure code heatmap
- calibration drift chart
- source contribution trend
- paper/live divergence chart

### Actions
- open linked dossier
- spawn replay
- propose source candidate
- mark manual review

## 10.8 Plugin Admin Page

### Purpose
将来 plugin を増やしても governance を保つ。

### Components
- plugin registry table
- plugin manifest viewer
- capability matrix
- enabled environments
- health status
- safe disable action

## 10.9 Interaction Contracts

UI actions は直接 DB を触らない。  
すべて action API へ送る。

例:
- `requestManualPrompt(decisionId)`
- `acceptPromptResponse(taskId, responseId)`
- `promoteSourceCandidate(candidateId)`
- `activateKillSwitch(scope, reason)`
