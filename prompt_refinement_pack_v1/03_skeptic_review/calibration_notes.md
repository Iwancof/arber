# skeptic_review calibration notes

## Intent
This prompt exists to penalize overconfidence and shallow narratives.

## Why confidence can only stay flat or go down
The primary forecast already had the opportunity to be optimistic. The skeptic stage should be strictly adversarial. Any upward revision belongs in a separate reconciliation stage, not in the skeptic.

## Adjustment scale
- `0.00`: forecast is reasonably calibrated
- `-0.02`: minor nit
- `-0.05`: one meaningful but not fatal concern
- `-0.10`: enough weakness that the operator or policy should pause or downsize
- `-0.15`: strong reason not to trust the trade
- `-0.20`: reject

## Common triggers for stronger downward adjustments
- macro event being treated as firm-specific edge without a clear factor link
- headline-only evidence for a supposedly high-confidence forecast
- benchmark mismatch
- short-term mechanical event projected too confidently into 5d
- alternative explanation ignored

## Recommendation mapping
- proceed: no material challenge
- reduce_size: still possibly valid, but edge is weaker than advertised
- wait: important uncertainty remains
- reject: not tradable in current form
