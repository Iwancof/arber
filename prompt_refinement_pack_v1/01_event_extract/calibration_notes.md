# event_extract calibration notes

## Intent
This prompt is designed to fix three failure modes:
1. free-form `event_type` drift,
2. over-extraction from noisy articles,
3. materiality values without common anchors.

## Why a fixed taxonomy
Downstream forecasting and analytics depend on comparing like with like. A controlled taxonomy is more important than perfect semantic nuance. The correct tradeoff for v1 is:
- slightly lossy categories,
- high consistency,
- zero free naming.

## Why `events: []` is the correct response for noise
If the document contains no new market-moving fact, emitting a low-quality event pollutes the pipeline and burns forecast calls. Empty is preferred to weak.

## Materiality anchors
The model should treat `materiality` as tradability over 1d–5d, not “how interesting is this article.”

### Quick anchors
- Ranking article / sector roundup → `0.00–0.15`
- Generic analyst commentary with no new number → `0.15–0.30`
- Named upgrade/downgrade with target change → `0.30–0.55`
- Earnings beat / miss → `0.60–0.75`
- Guidance raise / cut → `0.70–0.85`
- M&A target, FDA binary decisions → `0.80–0.95`

## Affected assets
For company-specific news:
- direct issuer tickers only

For macro news:
- broad proxies may be used if no single issuer is central

Do NOT infer sector ETFs inside event extraction unless the document explicitly frames the sector.

## Multi-event policy
Use one event by default.
Use two only when both are:
- explicit,
- independently market-moving,
- necessary to preserve interpretation.
