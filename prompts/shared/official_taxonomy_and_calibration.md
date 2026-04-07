# Official Event Taxonomy and Calibration

This document defines the fixed event taxonomy and shared calibration guidance used across the prompt set.

## 1. Event taxonomy

Only the following `event_type` values are valid in v1.

### Corporate (`corp_*`)
- `corp_earnings_beat`
- `corp_earnings_miss`
- `corp_guidance_raise`
- `corp_guidance_cut`
- `corp_buyback_authorized`
- `corp_dividend_raise`
- `corp_dividend_cut`
- `corp_mna_target`
- `corp_mna_acquirer`
- `corp_contract_win_major`
- `corp_contract_loss_major`
- `corp_product_launch_major`
- `corp_product_issue_or_recall`
- `corp_executive_change_material`
- `corp_financing_dilution`
- `corp_financing_refinancing_positive`
- `corp_bankruptcy_or_distress`
- `corp_operational_disruption`

### Regulatory / legal (`reg_*`)
- `reg_fda_approval`
- `reg_fda_delay_or_rejection`
- `reg_litigation_favorable`
- `reg_litigation_adverse`
- `reg_antitrust_or_enforcement`
- `reg_trade_restriction_or_sanction`

### Macro (`macro_*`)
- `macro_inflation_hot`
- `macro_inflation_cool`
- `macro_jobs_hot`
- `macro_jobs_cool`
- `macro_growth_hot`
- `macro_growth_cool`
- `macro_central_bank_hawkish`
- `macro_central_bank_dovish`
- `macro_treasury_auction_weak`
- `macro_treasury_auction_strong`

### Market structure / flows (`market_*`)
- `market_index_inclusion`
- `market_index_exclusion`
- `market_short_report`
- `market_activist_stake`
- `market_analyst_upgrade_material`
- `market_analyst_downgrade_material`

If a document contains no concrete new fact that maps to one of the above, return `events: []`.
Do not invent a new `event_type`.

## 2. Materiality calibration

`materiality` is the expected *tradability* of the event for U.S. equities over roughly 1d–5d, not merely how interesting the article sounds.

### Shared scale
- `0.00–0.15`: no tradable content; rankings, opinion, education, recaps, generic commentary
- `0.16–0.30`: minor factual update, weak catalyst, likely not enough for a reliable single-name edge
- `0.31–0.45`: real but modest catalyst; may matter only if combined with prior context
- `0.46–0.60`: clearly new company/event information; could matter, but magnitude is uncertain
- `0.61–0.75`: clear tradable catalyst with likely same-day/1–5d price discovery
- `0.76–0.90`: major catalyst with direct repricing implications
- `0.91–1.00`: rare systemic or transformative event

### Event-family anchors
- Earnings beat/miss with no guidance change: usually `0.60–0.75`
- Guidance raise/cut: usually `0.70–0.85`
- M&A target: usually `0.80–0.95`
- M&A acquirer: usually `0.55–0.75`
- FDA approval/rejection: usually `0.75–0.95`
- Analyst upgrade/downgrade: usually `0.30–0.55`, unless paired with material estimate/target changes
- Index inclusion/exclusion: usually `0.55–0.75`
- Macro release for single-name forecasting: event may be highly material in aggregate, but relative single-name edge is often weaker

## 3. Novelty calibration

`novelty` measures whether the article introduces *new* information relative to what was likely already known.

- `0.00–0.15`: stale / recap / old information
- `0.16–0.35`: routine follow-up or unsurprising continuation
- `0.36–0.55`: real new fact, but not very surprising
- `0.56–0.75`: materially new information or a meaningful update
- `0.76–0.90`: highly new and likely not widely priced
- `0.91–1.00`: unprecedented or highly unusual

## 4. Benchmark guidance

Default benchmark for v1 is `SPY`.

Use a sector ETF only when the calling layer explicitly provides it. Do not infer a sector ETF inside `event_extract`.

For macro events, relative single-name forecasting should be cautious:
- If the symbol’s factor sensitivity is not obvious from common public knowledge, remain near neutral vs benchmark.
- Macro events often move both the symbol and the benchmark; the relative edge is what matters.

## 5. Confidence anchor bands for forecasting

`confidence_after` is confidence that there is a *non-trivial relative edge vs benchmark* after considering counterarguments.

- `0.50–0.52`: effectively no edge / no trade / routine noise
- `0.53–0.57`: weak edge
- `0.58–0.64`: modest but usable edge
- `0.65–0.72`: clear edge
- `0.73–0.80`: strong edge
- `>0.80`: very rare; use only for hard, direct, primary-source catalysts with limited ambiguity

`confidence_after` should usually be less than or equal to `confidence_before`.

## 6. Noise patterns

Return `events: []` or classify as `noise` for:
- listicles, rankings, “top X stocks”
- broad sector roundups with no new hard fact
- generic market commentary
- educational articles
- rehashed old news
- “shares are up/down today” without a new catalyst
- descriptive price action with no underlying new fact
- interview/opinion pieces without new commitments, figures, or decisions

## 7. Multi-event rule

Default to **one primary event**.

Emit a second event only if:
1. it is explicitly stated in the document,
2. it is independently market-moving, and
3. it changes the interpretation (e.g., earnings miss **and** guidance cut; M&A **and** financing dilution).
