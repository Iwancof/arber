# noise_classifier calibration notes

## Intent
This classifier exists to reduce unnecessary expensive LLM calls.

## Preferred operating mode
- `signal` → always send to event extraction
- `noise` → drop by default
- `uncertain` → route to event extraction if cheap enough or if source is trusted/high-priority

## Why `uncertain` matters
Some of the most expensive mistakes come from forcing a binary choice on ambiguous headlines.
Examples:
- "Shares are trading lower Monday. Here's why."
- "Analyst reacts to ..."
- "Company announces update"

These can hide real signals or be empty wrappers. `uncertain` prevents the gate from becoming too aggressive.

## Good signal examples
- "Pfizer cuts 2026 EPS guidance"
- "Apple to acquire startup X for $3 billion"
- "FDA approves..."
- "CPI rises above expectations"

## Good noise examples
- "7 semiconductor stocks to watch"
- "Why investors love AI"
- "Stocks making moves midday" without a concrete catalyst
