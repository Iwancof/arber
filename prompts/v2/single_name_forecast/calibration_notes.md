# single_name_forecast calibration notes

## Intent
This prompt is designed to improve:
1. mechanism-based reasoning,
2. benchmark-relative thinking,
3. confidence calibration,
4. noise handling.

## What this forecast means
This is **not** a point-price forecast.
It is a forecast of whether the stock will outperform or underperform a benchmark over 1d and 5d.

## Recommended operational interpretation

### Confidence bands
- `0.50–0.52`: no edge; treat as no_trade
- `0.53–0.57`: weak edge; usually no_trade or review
- `0.58–0.64`: modest but usable edge
- `0.65–0.72`: clear edge
- `0.73–0.80`: strong edge
- `>0.80`: rare

These anchors are intentionally conservative to reduce false positives.

## Why confidence bunching happens
Models bunch around `0.50–0.60` when:
- the benchmark is not explicit,
- the event is not obviously firm-specific,
- there is no instruction to prefer neutral over fake precision,
- the model is allowed to narrate without calibrating.

This prompt fixes that by:
- forcing benchmark-relative reasoning,
- requiring competing hypotheses,
- anchoring confidence bands,
- forcing no-edge behavior for routine events.

## Benchmark guidance
Default benchmark is `SPY`.

Use benchmark-relative logic:
- company-specific earnings/guidance → firm-specific edge can be meaningful
- macro events → only meaningful if the stock has a clear factor loading
- broad market headlines with no clear differential → near-neutral vs SPY

## Hypothesis quality
Good:
- "guidance raise changes the forward revenue path and leads to a relative repricing vs SPY"

Bad:
- "bullish sentiment may help the stock"

## Counterargument expectations
Use concrete, tradable objections:
- already priced
- benchmark_shared_exposure
- macro_override
- weak magnitude
- time_horizon_mismatch
- insufficient_evidence

## No-edge behavior
If the event is routine or not benchmark-differentiated, the model should explicitly produce:
- `confidence_after` around `0.50–0.52`
- `p_outperform` around `0.49–0.51`
- quantiles centered near zero relative return
